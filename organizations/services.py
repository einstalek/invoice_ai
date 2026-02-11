from organizations.models import OrganizationMembership


def get_active_membership(user):
    return (
        OrganizationMembership.objects.select_related("organization")
        .filter(user=user, is_active=True)
        .first()
    )
