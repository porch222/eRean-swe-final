from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True


    dependencies = []


    operations = [

        migrations.CreateModel(

            name="Course",

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

                ("description", models.TextField()),

                ("category", models.CharField(max_length=100)),

                (

                    "status",

                    models.CharField(

                        choices=[

                            ("draft", "Draft"),

                            ("published", "Published"),

                            ("archived", "Archived"),

                        ],

                        default="draft",

                        max_length=20,

                    ),

                ),

                ("created_at", models.DateTimeField(auto_now_add=True)),

            ],

        ),

        migrations.CreateModel(

            name="Material",

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

                (

                    "type",

                    models.CharField(

                        choices=[("video", "Video"), ("pdf", "PDF"), ("link", "Link")],

                        max_length=20,

                    ),

                ),

                ("file_url", models.FileField(upload_to="materials/")),

                ("uploaded_at", models.DateTimeField(auto_now_add=True)),

            ],

        ),

    ]
