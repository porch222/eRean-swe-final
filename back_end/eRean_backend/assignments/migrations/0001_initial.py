from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True


    dependencies = []


    operations = [

        migrations.CreateModel(

            name="Assignment",

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

                (

                    "type",

                    models.CharField(

                        choices=[("assignment", "Assignment"), ("quiz", "Quiz")],

                        default="assignment",

                        max_length=20,

                    ),

                ),

                ("due_date", models.DateTimeField(blank=True, null=True)),

                ("max_score", models.IntegerField(default=100)),

                ("created_at", models.DateTimeField(auto_now_add=True)),

            ],

        ),

        migrations.CreateModel(

            name="Submission",

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

                (

                    "file_url",

                    models.FileField(blank=True, null=True, upload_to="submissions/"),

                ),

                (

                    "grade",

                    models.DecimalField(

                        blank=True, decimal_places=2, max_digits=5, null=True

                    ),

                ),

                ("feedback", models.TextField(blank=True, null=True)),

                ("submitted_at", models.DateTimeField(auto_now_add=True)),

            ],

        ),

    ]
