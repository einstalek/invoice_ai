import re
from typing import Optional


class CountryCode:
    EE = "EE"
    EU_OTHER = "EU_OTHER"
    NON_EU = "NON_EU"


class SupplyType:
    GOODS = "GOODS"
    SERVICES = "SERVICES"


class Scenario:
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class ServiceType:
    SERV_9 = "SERV_9"
    SERV_13 = "SERV_13"
    SERV_24 = "SERV_24"
    SERV_0 = "SERV_0"
    SERV_EX = "SERV_EX"


class DomesticScenario:
    EE_DOM_24_STD = "EE_DOM_24_STD"
    EE_DOM_13_ACC = "EE_DOM_13_ACC"
    EE_DOM_9_REDUCED = "EE_DOM_9_REDUCED"
    EE_DOM_0_TAXABLE = "EE_DOM_0_TAXABLE"
    EE_DOM_EXEMPT = "EE_DOM_EXEMPT"


class EUScenario:
    EU_GOODS_ICS_9_FULL = "EU_GOODS_ICS_9_FULL"
    EU_GOODS_ICS_24_FULL = "EU_GOODS_ICS_24_FULL"
    EU_SERV_RC_9_FULL = "EU_SERV_RC_9_FULL"
    EU_SERV_RC_24 = "EU_SERV_RC_24"
    EU_FOREIGN_VAT_COST_ONLY = "EU_FOREIGN_VAT_COST_ONLY"


class NonEUScenario:
    NON_EU_SERV_RC_24_FULL = "NON_EU_SERV_RC_24_FULL"
    NON_EU_SERV_RC_9_FULL = "NON_EU_SERV_RC_9_FULL"
    NON_EU_IMPORT_KMD_24 = "NON_EU_IMPORT_KMD_24"
    NON_EU_IMPORT_KMD_9 = "NON_EU_IMPORT_KMD_9"


def determine_vat_scenarios(response: dict) -> Optional[str]:
    buyer_ccode = response.get("buyer_country_group", {}).get("value")
    if not buyer_ccode:
        return None
    supplier_ccode = response.get("supplier_country_group", {}).get("value")
    if not supplier_ccode:
        return None
    supply_type = response.get("supply_type", {}).get("value")
    if not supply_type:
        return None
    service_type = (
        response.get("service_category", {}).get("value")
        if supply_type == SupplyType.SERVICES
        else None
    )
    vat_rates = response.get("vat_rates", {}).get("value", "")
    supplier_vat_id = response.get("supplier_vat_id", {}).get("value", "")

    def _extract_rate_numbers(value):
        if value is None:
            return []
        if isinstance(value, (int, float)):
            return [float(value)]
        if isinstance(value, list):
            numbers = []
            for item in value:
                numbers.extend(_extract_rate_numbers(item))
            return numbers
        if isinstance(value, str):
            matches = re.findall(r"\d+(?:[.,]\d+)?", value)
            return [float(m.replace(",", ".")) for m in matches]
        return []

    def _has_zero_rate(value):
        return any(abs(rate) < 1e-9 for rate in _extract_rate_numbers(value))

    if not buyer_ccode == CountryCode.EE:
        return Scenario.OUT_OF_SCOPE

    # ==================== EE supplier ====================
    if supplier_ccode == CountryCode.EE:
        if supply_type == SupplyType.SERVICES:
            if service_type == ServiceType.SERV_9:
                return DomesticScenario.EE_DOM_9_REDUCED
            if service_type == ServiceType.SERV_13:
                return DomesticScenario.EE_DOM_13_ACC
            if service_type == ServiceType.SERV_EX:
                return DomesticScenario.EE_DOM_EXEMPT
            if service_type == ServiceType.SERV_0:
                return DomesticScenario.EE_DOM_0_TAXABLE
            if service_type == ServiceType.SERV_24 or service_type is None:
                return DomesticScenario.EE_DOM_24_STD
            return DomesticScenario.EE_DOM_24_STD  # default
        elif supply_type == SupplyType.GOODS:
            if service_type == ServiceType.SERV_9:
                return DomesticScenario.EE_DOM_9_REDUCED
            if service_type == ServiceType.SERV_13:
                return DomesticScenario.EE_DOM_13_ACC
            return DomesticScenario.EE_DOM_24_STD

    # ==================== EU SUPPLIER ====================
    elif supplier_ccode == CountryCode.EU_OTHER:
        has_foreign_vat = supplier_vat_id and not supplier_vat_id.startswith("EE")
        if supply_type == SupplyType.GOODS:
            if service_type == ServiceType.SERV_9:
                return EUScenario.EU_GOODS_ICS_9_FULL
            else:
                return EUScenario.EU_GOODS_ICS_24_FULL

        elif supply_type == SupplyType.SERVICES:
            if has_foreign_vat and vat_rates and not _has_zero_rate(vat_rates):
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
    return None
