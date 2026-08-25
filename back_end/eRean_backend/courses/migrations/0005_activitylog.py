import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ("courses", "0004_announcement"),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.CreateModel(

            name="ActivityLog",

            fields=[

                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),

                ("action", models.CharField(max_length=100)),

                ("target_type", models.CharField(blank=True, max_length=100)),

                ("target_id", models.PositiveIntegerField(blank=True, null=True)),

                ("details", models.TextField(blank=True)),

                ("created_at", models.DateTimeField(auto_now_add=True)),

                (

                    "actor",

                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activity_logs", to=settings.AUTH_USER_MODEL),

                ),

            ],

        ),

    ]
