import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ("assignments", "0003_initial"),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.CreateModel(

            name="QuizAttempt",

            fields=[

                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),

                ("score", models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),

                ("submitted_at", models.DateTimeField(auto_now_add=True)),

                (

                    "assignment",

                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_attempts", to="assignments.assignment"),

                ),

                (

                    "student",

                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_attempts", to=settings.AUTH_USER_MODEL),

                ),

            ],

        ),

        migrations.CreateModel(

            name="QuizQuestion",

            fields=[

                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),

                ("text", models.TextField()),

                ("points", models.PositiveIntegerField(default=1)),

                ("order", models.PositiveIntegerField(default=0)),

                (

                    "assignment",

                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="assignments.assignment"),

                ),

            ],

        ),

        migrations.CreateModel(

            name="QuizChoice",

            fields=[

                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),

                ("text", models.CharField(max_length=500)),

                ("is_correct", models.BooleanField(default=False)),

                ("order", models.PositiveIntegerField(default=0)),

                (

                    "question",

                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="assignments.quizquestion"),

                ),

            ],

        ),

        migrations.CreateModel(

            name="QuizAnswer",

            fields=[

                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),

                ("is_correct", models.BooleanField(default=False)),

                (

                    "attempt",

                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="assignments.quizattempt"),

                ),

                (

                    "question",

                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="assignments.quizquestion"),

                ),

                (

                    "selected_choice",

                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="assignments.quizchoice"),

                ),

            ],

        ),

        migrations.AlterUniqueTogether(

            name="quizattempt",

            unique_together={("assignment", "student")},

        ),

        migrations.AlterUniqueTogether(

            name="quizanswer",

            unique_together={("attempt", "question")},

        ),

    ]
