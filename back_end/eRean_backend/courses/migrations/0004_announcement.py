import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ("courses", "0003_material_link_url_alter_material_file_url"),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.CreateModel(

            name="Announcement",

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

                ("title", models.CharField(max_length=200)),

                ("content", models.TextField()),

                ("created_at", models.DateTimeField(auto_now_add=True)),

                (

                    "author",

                    models.ForeignKey(

                        on_delete=django.db.models.deletion.CASCADE,

                        related_name="announcements",

                        to=settings.AUTH_USER_MODEL,

                    ),

                ),

                (

                    "course",

                    models.ForeignKey(

                        on_delete=django.db.models.deletion.CASCADE,

                        related_name="announcements",

                        to="courses.course",

                    ),

                ),

            ],

        ),

    ]
