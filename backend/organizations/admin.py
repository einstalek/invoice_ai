from django.contrib import admin

from .models import Organization, OrganizationMembership, Supplier


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "erp_type", "required_approvals", "created_at")
    search_fields = ("name", "vat_number")


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("invited_email", "organization", "role", "status", "user", "created_at")
    list_filter = ("role", "status")
    search_fields = ("invited_email",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "vat_id", "country", "country_group")
    search_fields = ("name", "vat_id")
    list_filter = ("country_group",)
