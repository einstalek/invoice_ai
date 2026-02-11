from django.contrib import admin

from .models import Organization, OrganizationInvite, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "created_by")
    search_fields = ("name",)


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("organization__name", "user__email", "user__username")


@admin.register(OrganizationInvite)
class OrganizationInviteAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "email", "status", "invited_by", "created_at")
    list_filter = ("status",)
    search_fields = ("organization__name", "email")
