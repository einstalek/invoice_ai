from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_organizationinvite"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="organizationinvite",
            name="token",
        ),
    ]
