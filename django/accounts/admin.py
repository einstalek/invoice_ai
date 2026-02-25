from django.contrib import admin

from .models import GoogleCredential, UserPreference


@admin.register(GoogleCredential)
class GoogleCredentialAdmin(admin.ModelAdmin):
    list_display = ("user", "spreadsheet_id", "updated_at", "created_at")
    search_fields = ("user__email", "user__username", "spreadsheet_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "updated_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("updated_at",)
