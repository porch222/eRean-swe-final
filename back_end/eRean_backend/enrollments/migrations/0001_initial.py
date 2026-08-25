import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True


    dependencies = [

        ("courses", "0001_initial"),

    ]


    operations = [

        migrations.CreateModel(

            name="Enrollment",

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

                    "status",

                    models.CharField(

                        choices=[

                            ("active", "Active"),

                            ("dropped", "Dropped"),

                            ("completed", "Completed"),

                        ],

                        default="active",

                        max_length=20,

                    ),

                ),

                (

                    "progress",

                    models.DecimalField(decimal_places=2, default=0.0, max_digits=5),

                ),

                ("enrolled_at", models.DateTimeField(auto_now_add=True)),

                (

                    "course",

                    models.ForeignKey(

                        on_delete=django.db.models.deletion.CASCADE,

                        related_name="enrollments",

                        to="courses.course",

                    ),

                ),

            ],

        ),

    ]
