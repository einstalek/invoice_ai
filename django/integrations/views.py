from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.services import get_user_credentials, set_user_spreadsheet_id
from google_sheets_utils import create_user_spreadsheet, get_user_spreadsheet_title


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class SelectSheetView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Google account not connected."}, status=401)
        spreadsheet_id = (request.data.get("spreadsheet_id") or "").strip()
        if not spreadsheet_id:
            return Response({"error": "Missing spreadsheet id."}, status=400)
        set_user_spreadsheet_id(request.user, spreadsheet_id)
        return Response({"ok": True, "spreadsheet_id": spreadsheet_id})


class CreateSheetView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Google account not connected."}, status=401)
        credentials, _ = get_user_credentials(request.user)
        if not credentials:
            return Response({"error": "Google account not connected."}, status=401)

        title = request.data.get("title")
        spreadsheet_id = create_user_spreadsheet(credentials, title)
        set_user_spreadsheet_id(request.user, spreadsheet_id)

        spreadsheet_title = title
        if not spreadsheet_title:
            try:
                spreadsheet_title = get_user_spreadsheet_title(credentials, spreadsheet_id)
            except Exception:
                spreadsheet_title = None

        return Response(
            {
                "ok": True,
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_title": spreadsheet_title,
                "spreadsheet_rows": 0,
            }
        )
