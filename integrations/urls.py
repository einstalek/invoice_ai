from django.urls import path

from . import views


urlpatterns = [
    path("auth/google/sheet", views.SelectSheetView.as_view(), name="select_sheet"),
    path("auth/google/create-sheet", views.CreateSheetView.as_view(), name="create_sheet"),
]
