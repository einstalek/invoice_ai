from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0003_invoice_submission_comment"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvoiceReviewAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("declined", "Declined"), ("changes_requested", "Changes requested")], default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="invoice_review_assignments_created", to=settings.AUTH_USER_MODEL)),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invoice_review_assignments", to=settings.AUTH_USER_MODEL)),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="review_assignments", to="invoices.invoicesubmission")),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("submission", "reviewer"), name="unique_invoice_review_assignment")
                ],
            },
        ),
    ]
