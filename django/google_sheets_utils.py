import json
import os
from datetime import datetime
from typing import Any, Iterable, Optional

import dotenv

dotenv.load_dotenv()

import gspread


OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_user_worksheet(
    credentials, spreadsheet_id: str, worksheet_name: Optional[str] = None
):
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(spreadsheet_id)
    return sheet.worksheet(worksheet_name) if worksheet_name else sheet.sheet1


def get_user_spreadsheet_title(credentials, spreadsheet_id: str) -> str:
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(spreadsheet_id)
    return sheet.title


def get_user_filled_row_count(
    credentials,
    spreadsheet_id: str,
    worksheet_name: Optional[str] = None,
) -> int:
    ws = get_user_worksheet(credentials, spreadsheet_id, worksheet_name)
    values = ws.get_all_values()
    if not values:
        return 0
    return max(len(values) - 1, 0)


def create_user_spreadsheet(credentials, title: Optional[str] = None) -> str:
    client = gspread.authorize(credentials)
    sheet_title = title or f"Invoice OCR {datetime.utcnow().strftime('%Y-%m-%d')}"
    sheet = client.create(sheet_title)
    return sheet.id


def _normalize_value(value: Any) -> str:
    if isinstance(value, dict) and "value" in value:
        value = value["value"]
    if value is None:
        return "None"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def append_invoice_row_with_credentials(
    credentials,
    spreadsheet_id: str,
    invoice: dict,
    fields: Iterable[str],
    worksheet_name: Optional[str] = None,
    ensure_header: bool = True,
) -> None:
    ws = get_user_worksheet(credentials, spreadsheet_id, worksheet_name)

    field_list = list(fields)
    if ensure_header:
        existing = ws.row_values(1)
        if existing:
            field_list = existing
        else:
            ws.append_row(field_list, value_input_option="USER_ENTERED")

    row = [_normalize_value(invoice.get(field)) for field in field_list]
    ws.append_row(row, value_input_option="USER_ENTERED")


def append_invoice_to_user_sheet(
    credentials, spreadsheet_id: str, invoice: dict
) -> None:
    fields_env = os.getenv("GOOGLE_SHEETS_FIELDS")
    fields = (
        [f.strip() for f in fields_env.split(",") if f.strip()]
        if fields_env
        else list(invoice.keys())
    )

    append_invoice_row_with_credentials(
        credentials=credentials,
        spreadsheet_id=spreadsheet_id,
        invoice=invoice,
        fields=fields,
        worksheet_name=os.getenv("GOOGLE_SHEETS_WORKSHEET"),
    )
