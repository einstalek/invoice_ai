from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("invoices", "0004_invoice_review_assignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoicesubmission",
            name="exported_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="invoicesubmission",
            name="exported_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invoice_exports",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
