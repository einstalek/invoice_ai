from dotenv import load_dotenv
load_dotenv()

import replicate
import json
from typing import Optional
from pathlib import Path
from docling.document_converter import DocumentConverter
from prompts import system_prompt_parse_w_reasoning


class CountryCode:
    EE = 'EE'
    EU_OTHER = 'EU_OTHER'
    NON_EU = 'NON_EU'

class SupplyType:
    GOODS = 'GOODS'
    SERVICES = 'SERVICES'


class Scenario:
    OUT_OF_SCOPE = 'OUT_OF_SCOPE'

class ServiceType:
    SERV_9 = 'SERV_9'
    SERV_13 = 'SERV_13'
    SERV_24 = 'SERV_24'
    SERV_0 = 'SERV_0' 
    SERV_EX = 'SERV_EX'


class DomesticScenario:
    EE_DOM_24_STD = 'EE_DOM_24_STD'
    EE_DOM_13_ACC = 'EE_DOM_13_ACC'
    EE_DOM_9_REDUCED = 'EE_DOM_9_REDUCED'
    EE_DOM_0_TAXABLE = 'EE_DOM_0_TAXABLE'
    EE_DOM_EXEMPT = 'EE_DOM_EXEMPT'


class EUScenario:
    EU_GOODS_ICS_9_FULL = 'EU_GOODS_ICS_9_FULL'
    EU_GOODS_ICS_24_FULL = 'EU_GOODS_ICS_24_FULL'
    EU_SERV_RC_9_FULL = 'EU_SERV_RC_9_FULL'
    EU_SERV_RC_24 = 'EU_SERV_RC_24'
    EU_FOREIGN_VAT_COST_ONLY = 'EU_FOREIGN_VAT_COST_ONLY'

class NonEUScenario:
    NON_EU_SERV_RC_24_FULL = 'NON_EU_SERV_RC_24_FULL'
    NON_EU_SERV_RC_9_FULL = 'NON_EU_SERV_RC_9_FULL'
    NON_EU_IMPORT_KMD_24 = 'NON_EU_IMPORT_KMD_24'
    NON_EU_IMPORT_KMD_9 = 'NON_EU_IMPORT_KMD_9'


def run_ocr(filepath: Path) -> str:
    global pdf_converter
    if pdf_converter is None:
        pdf_converter = DocumentConverter()
    result = pdf_converter.convert(filepath, max_num_pages=10)
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


def pipeline(filepath: Path) -> dict:
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
        result_dict[k] = {'value': v, 'bbox': None}

    final_response = {}
    for k, v in result_dict.items():
        if 'reasoning' in k:
            continue
        if type(v) is str and not v.strip():
            continue
        if type(v) is list and not v:
            continue
        if isinstance(v, dict) and 'value' in v:
            final_response[k] = v
        else:
            final_response[k] = { "value": v, "bbox": None }

    final_response['scenario'] = determine_vat_scenarios(final_response)
    return final_response


def determine_vat_scenarios(response: dict) -> Optional[str]:
    buyer_ccode = response.get('buyer_country_group', {}).get('value')
    assert buyer_ccode
    supplier_ccode = response.get('supplier_country_group', {}).get('value')
    assert supplier_ccode
    supply_type = response.get('supply_type', {}).get('value')
    assert supply_type
    service_type = response.get('service_category', {}).get('value') if supply_type == SupplyType.SERVICES else None
    vat_rates = response.get('vat_rates', {}).get('value', '')
    supplier_vat_id = response.get('supplier_vat_id', {}).get('value', '')

    if not buyer_ccode == CountryCode.EE:
        return Scenario.OUT_OF_SCOPE

    # ==================== EE supplier ====================
    if supplier_ccode == CountryCode.EE:
        if supply_type == SupplyType.SERVICES:
            if service_type == ServiceType.SERV_9: return DomesticScenario.EE_DOM_9_REDUCED
            if service_type == ServiceType.SERV_13: return DomesticScenario.EE_DOM_13_ACC
            if service_type == ServiceType.SERV_EX: return DomesticScenario.EE_DOM_EXEMPT
            if service_type == ServiceType.SERV_0: return DomesticScenario.EE_DOM_0_TAXABLE
            if service_type == ServiceType.SERV_24 or service_type is None: return DomesticScenario.EE_DOM_24_STD
            return DomesticScenario.EE_DOM_24_STD  # default
        elif supply_type == SupplyType.GOODS:
            if service_type == ServiceType.SERV_9: return DomesticScenario.EE_DOM_9_REDUCED
            if service_type == ServiceType.SERV_13: return DomesticScenario.EE_DOM_13_ACC
            return DomesticScenario.EE_DOM_24_STD
    

    # ==================== EU SUPPLIER ====================
    elif supplier_ccode == CountryCode.EU_OTHER:
        has_foreign_vat = supplier_vat_id and not supplier_vat_id.startswith('EE')
        if supply_type == SupplyType.GOODS:
            if service_type == ServiceType.SERV_9:
                return EUScenario.EU_GOODS_ICS_9_FULL
            else:
                return EUScenario.EU_GOODS_ICS_24_FULL
    
        elif supply_type == SupplyType.SERVICES:
            if has_foreign_vat and vat_rates and '0' not in vat_rates:
                return EUScenario.EU_FOREIGN_VAT_COST_ONLY
            else:
                if service_type == ServiceType.SERV_9:
                    return EUScenario.EU_SERV_RC_9_FULL
                else:
                    return EUScenario.EU_SERV_RC_24
        return Scenario.OUT_OF_SCOPE


    # ==================== NON EU SUPPLIER ====================
    elif supplier_ccode == CountryCode.NON_EU:
        if supply_type == SupplyType.GOODS:
            if service_type == ServiceType.SERV_9:
                return NonEUScenario.NON_EU_IMPORT_KMD_9
            else:
                return NonEUScenario.NON_EU_IMPORT_KMD_24
        elif supply_type == SupplyType.SERVICES:
            if service_type == ServiceType.SERV_9:
                return NonEUScenario.NON_EU_SERV_RC_9_FULL
            else:
                return NonEUScenario.NON_EU_SERV_RC_24_FULL
        return Scenario.OUT_OF_SCOPE
    else:
        raise ValueError("Unknown country code")


pdf_converter = None
