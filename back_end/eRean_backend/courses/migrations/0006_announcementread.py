import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ("courses", "0005_activitylog"),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.CreateModel(

            name="AnnouncementRead",

            fields=[

                (

                    "id",

                    models.BigAutoField(

                        auto_created=True,

                        primary_key=True,

                        serialize=False,

                        verbose_name="ID",

                    ),

                ),

                ("read_at", models.DateTimeField(auto_now_add=True)),

                (

                    "announcement",

                    models.ForeignKey(

                        on_delete=django.db.models.deletion.CASCADE,

                        related_name="reads",

                        to="courses.announcement",

                    ),

                ),

                (

                    "student",

                    models.ForeignKey(

                        on_delete=django.db.models.deletion.CASCADE,

                        related_name="announcement_reads",

                        to=settings.AUTH_USER_MODEL,

                    ),

                ),

            ],

            options={

                "unique_together": {("announcement", "student")},

            },

        ),

    ]
