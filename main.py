from PIL import Image
from sympy import im
import torch
import json
from pathlib import Path
from typing import List, Sequence, Tuple
from pdf2image import convert_from_path, convert_from_bytes
from transformers import AutoModelForCausalLM, AutoProcessor, AutoTokenizer
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
from prompts import (system_prompt_buyer, 
                     system_prompt_supplier, 
                     system_prompt_vat, 
                     system_prompt_parse, 
                     system_prompt_summary)

from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator


def resize(image, min_w=648):
    w, h = image.size

    min_size = min(min_w, min(h, w))

    scale = min(h, w) / min_size

    image_resized = image.resize((int(w/scale), int(h/scale)))
    image_resized.size
    return image_resized


def pdf2image(filepath: Path) -> List[Image.Image]:
    return convert_from_path(filepath)


def load_models(ocr_provider, device):
    if ocr_provider == 'paddle':
        model_path = "PaddlePaddle/PaddleOCR-VL"
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            trust_remote_code=True, 
            torch_dtype=torch.bfloat16,
        ).to(device).eval()
        processor = AutoProcessor.from_pretrained(model_path, 
                                                trust_remote_code=True)
    elif ocr_provider == 'doctr':
        model = ocr_predictor(pretrained=True).to(device)
        processor = None
    elif ocr_provider == 'pdfminer':
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        interpreter_device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, interpreter_device)
        model = interpreter
        processor = None

    # Question answering
    model_name = "Qwen/Qwen3-4B-Instruct-2507"

    llm = AutoModelForCausalLM.from_pretrained(
        model_name,
        # torch_dtype="auto",
        torch_dtype=torch.bfloat16,
        # device_map="auto"
    ).to(device).eval()

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, processor, llm, tokenizer


def run_ocr(*args, **kwargs) -> (str, list):
    if ocr_provider == 'paddle':
        return run_ocr_paddle(*args, **kwargs)
    elif ocr_provider == 'doctr':
        return run_ocr_doctr(*args, **kwargs)
    elif ocr_provider == 'pdfminer':
        return run_ocr_pdfminer(*args, **kwargs)


def run_ocr_pdfminer(pdf_filepath, model, processor, device):
    global H, W
    fp = open(pdf_filepath, 'rb')
    pages = PDFPage.get_pages(fp)

    outputs_total = ""
    bboxes = []
    for page in pages:
        # print('Processing next page...')
        model.process_page(page)
        layout = model.device.get_result()
        *_, w, h = layout.bbox
        W = w
        H = h
        for lobj in layout:
            if isinstance(lobj, LTTextBox):
                x, y, text = lobj.bbox[0], lobj.bbox[3], lobj.get_text()
                # print('At %r is text: %s' % ((x, y), text))
                outputs_total += text + '\n'
                bboxes.append([lobj.bbox, text])
    return outputs_total, bboxes


def run_ocr_doctr(pdf_filepath, model, processor, device):
    pdf_doc = DocumentFile.from_pdf(pdf_filepath)
    result = model(pdf_doc)
    outputs_total = result.render()
    return outputs_total, None


def run_ocr_paddle(pdf_filepath, model, processor, device):
    images = pdf2image(pdf_filepath), None

    CHOSEN_TASK = "ocr"  # Options: 'ocr' | 'table' | 'chart' | 'formula'
    PROMPTS = {
        "ocr": "OCR:",
        "table": "Table Recognition:",
        "formula": "Formula Recognition:",
        "chart": "Chart Recognition:",
    }
    CHOSEN_TASK = "ocr"  # Options: 'ocr' | 'table' | 'chart' | 'formula'

    outputs_total = ""
    for image in images:
        image_resized = resize(image, min_w=648)
        messages = [
            {"role": "user",         
            "content": [
                    {"type": "image", "image": image_resized},
                    {"type": "text", "text": PROMPTS[CHOSEN_TASK]},
                ]
            }
        ]
        inputs = processor.apply_chat_template(
            messages, 
            tokenize=True, 
            add_generation_prompt=True, 	
            return_dict=True,
            return_tensors="pt"
        ).to(device)

        outputs = model.generate(**inputs, max_new_tokens=1024)
        outputs = processor.batch_decode(outputs, skip_special_tokens=True)[0]

        outputs_total += "\n" + outputs
    return outputs_total


def run_reasoning(prompt, system_prompt, invoice_text, llm, tokenizer):
    if invoice_text is not None:
        prompt = f"""
        {prompt}
        Invoice: {invoice_text}.
        """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(llm.device)

    generated_ids = llm.generate(
        **model_inputs,
        max_new_tokens=32768,
    )

    decoded = tokenizer.batch_decode(generated_ids[:, model_inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
    return decoded


def pipeline(filepath, device):
    print('Step 1: Running OCR')
    invoice_text, bboxes = run_ocr(filepath, model, processor, device)

    print(invoice_text)
    print('-' * 30)

    reasoning = ""
    prompt = "Who is the legal entity that made the purchase, i.e. the buyer?"
    print('Step 2: Running reasoning for buyer')
    reasoning += run_reasoning(prompt, system_prompt_buyer, invoice_text, llm, tokenizer) + "\n"
    prompt = "Who is the legal entity that provided goods or services, i.e. the supplier?"
    print('Step 3: Running reasoning for supplier')
    reasoning += run_reasoning(prompt, system_prompt_supplier, invoice_text, llm, tokenizer)
    prompt = "What are the vat rates mentioned in this invoice? It could be one, multiple or none."
    print('Step 4: Running reasoning for vat rates')
    reasoning += run_reasoning(prompt, system_prompt_vat, invoice_text, llm, tokenizer)

    prompt = f"""Summarise this reasoning into one sentence. It must have the final verdict on buyer, supplier, and vat rates.
    Reasoning: {reasoning}"""
    reasoning_summary = run_reasoning(prompt, system_prompt_summary, None, llm, tokenizer)

    print(reasoning_summary)
    print('-' * 30)

    prompt = f"""
    Using the following reasoning previously extracted from invoice: {reasoning_summary}, 
    now extract specific fields from that invoice.
    Full invoice here: {invoice_text}.
    """

    messages = [
        {"role": "system", "content": system_prompt_parse},
        {"role": "user", "content": prompt}
    ]

    print('Step 5: Running json extraction')
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(llm.device)

    generated_ids = llm.generate(
        **model_inputs,
        max_new_tokens=32768,
    )

    decoded = tokenizer.batch_decode(generated_ids[:, model_inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
    # return decoded
    result_dict = json.loads(decoded)
    for (k, v) in result_dict.items():
        if not v:
            continue
        # bbox = [t for t in bboxes if v in t[-1]]
        # if len(bbox) > 0:
        #     bbox = bbox[0][0]
        #     x1, y1, x2, y2 = bbox
        #     result_dict[k] = {'value': v, 'bbox': [x1/W, y1/H, (x2-x1)/W, (y2-y1)/H]}
        # else:
        #     result_dict[k] = {'value': v, 'bbox': None}
        result_dict[k] = {'value': v, 'bbox': None}
    return result_dict


H = None
W = None
DEVICE = "cuda:2"
# ocr_provider = 'doctr'
ocr_provider = 'pdfminer'
model, processor, llm, tokenizer = load_models(ocr_provider, DEVICE)
