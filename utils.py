from dotenv import load_dotenv
import os

load_dotenv()

import replicate
import json
from typing import Optional
from pathlib import Path
import time

from django.core.cache import cache

# from docling.document_converter import DocumentConverter
from prompts import system_prompt_parse_w_reasoning

import pymupdf4llm
import fitz

from accounting_utils import *

# def run_ocr(filepath: Path) -> str:
#     global pdf_converter
#     try:
#         if pdf_converter is None:
#             pdf_converter = DocumentConverter()
#         result = pdf_converter.convert(filepath, max_num_pages=10)
#         outputs_total = result.document.export_to_markdown()
#     except Exception as e:
#         print(e)
#     return outputs_total


def run_ocr(filepath: Path):
    with fitz.open(filepath) as doc:
        page_count = doc.page_count
    if page_count <= 0:
        return ""
    max_pages = min(page_count, 10)
    pages = list(range(max_pages))
    md_text = pymupdf4llm.to_markdown(filepath, pages=pages)
    return md_text


PREDICTION_CACHE_PREFIX = "replicate_prediction"
PREDICTION_CACHE_TTL = 60 * 60
CANCEL_CACHE_PREFIX = "replicate_cancel"
CANCEL_CACHE_TTL = 60 * 60


class ReplicateCancelled(RuntimeError):
    pass


class ReplicateFailed(RuntimeError):
    pass


def get_prediction_cache_key(request_id: str) -> str:
    return f"{PREDICTION_CACHE_PREFIX}:{request_id}"

def get_cancel_cache_key(request_id: str) -> str:
    return f"{CANCEL_CACHE_PREFIX}:{request_id}"


def llm_request(prompt, request_id: Optional[str] = None):
    input = {"prompt": system_prompt_parse_w_reasoning + "\n" + prompt}

    prediction = replicate.predictions.create(
        # model="anthropic/claude-3.7-sonnet",  ## stronger reasoning, higher costs
        # model="meta/meta-llama-3-8b-instruct",
        model="qwen/qwen3-235b-a22b-instruct-2507",
        input=input,
    )

    if request_id:
        cache.set(get_prediction_cache_key(request_id), prediction.id, timeout=PREDICTION_CACHE_TTL)

    try:
        if request_id and cache.get(get_cancel_cache_key(request_id)):
            replicate.predictions.cancel(prediction.id)
            cache.delete(get_cancel_cache_key(request_id))
            raise ReplicateCancelled("Replicate prediction was canceled.")
        while prediction.status not in {"succeeded", "failed", "canceled"}:
            time.sleep(0.75)
            if request_id and cache.get(get_cancel_cache_key(request_id)):
                replicate.predictions.cancel(prediction.id)
                cache.delete(get_cancel_cache_key(request_id))
                raise ReplicateCancelled("Replicate prediction was canceled.")
            prediction = replicate.predictions.get(prediction.id)
    finally:
        if request_id:
            cache.delete(get_prediction_cache_key(request_id))
            cache.delete(get_cancel_cache_key(request_id))

    if prediction.status == "canceled":
        raise ReplicateCancelled("Replicate prediction was canceled.")
    if prediction.status != "succeeded":
        raise ReplicateFailed(prediction.error or "Replicate prediction failed.")

    output = prediction.output
    if isinstance(output, list):
        return "".join(output)
    if output is None:
        return ""
    return str(output)


def pipeline(filepath: Path, request_id: Optional[str] = None) -> dict:
    invoice_text = run_ocr(filepath)
    if not invoice_text or not invoice_text.strip():
        raise RuntimeError("OCR_EMPTY")

    prompt = f"""
    You need to read through an invoice text and fill in several fields in a json, following provided instructions.
    In each field '*_reasoning', provide explanations for your choices.
    Full invoice here: {invoice_text}.
    """
    output = llm_request(prompt, request_id=request_id)
    result_dict = json.loads(output)

    reasoning_fields = {
        k: v for k, v in result_dict.items() if isinstance(k, str) and "reasoning" in k
    }
    if reasoning_fields and os.getenv("LOG_LLM_REASONING") == "1":
        print("LLM reasoning fields:")
        print(json.dumps(reasoning_fields, indent=2, ensure_ascii=True))

    final_response = {}
    for k, v in result_dict.items():
        if isinstance(k, str) and "reasoning" in k:
            continue
        confidence = None
        if isinstance(v, dict):
            value = v.get("value")
            confidence = v.get("confidence")
        else:
            value = v

        if isinstance(value, str) and not value.strip() and not confidence:
            continue
        if isinstance(value, list) and not value and not confidence:
            continue
        if isinstance(value, dict) and not value and not confidence:
            continue

        payload = {"value": value}
        if confidence:
            payload["confidence"] = confidence
        final_response[k] = payload

    final_response["scenario"] = determine_vat_scenarios(final_response)
    return final_response
