from dotenv import load_dotenv
load_dotenv()

import replicate
import json
from pathlib import Path
from docling.document_converter import DocumentConverter
from prompts import system_prompt_parse_w_reasoning

def run_ocr(filepath: Path) -> str:
    global pdf_converter
    if pdf_converter is None:
        pdf_converter = DocumentConverter()
    result = pdf_converter.convert(filepath)
    outputs_total = result.document.export_to_markdown()
    return outputs_total


def llm_request(prompt):
    input = {
        "prompt": system_prompt_parse_w_reasoning + '\n' + prompt
    }

    output = replicate.run(
        "qwen/qwen3-235b-a22b-instruct-2507",
        input=input)
    return "".join(output)


def pipeline(filepath):
    print('Step 1: Running OCR')
    invoice_text = run_ocr(filepath)

    prompt = f"""
    You need to read through an invoice text and fill in several fields in a json, following provided instructions.
    In each field '*_reasoning', provide explanations for your choices.
    Full invoice here: {invoice_text}.
    """

    output = llm_request(prompt)
    
    # return decoded
    result_dict = json.loads(output)
    for (k, v) in result_dict.items():
        # if not v:
        #     continue
        result_dict[k] = {'value': v, 'bbox': None}
    return result_dict


pdf_converter = None
