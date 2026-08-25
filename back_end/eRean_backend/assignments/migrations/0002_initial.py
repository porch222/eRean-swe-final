import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True


    dependencies = [

        ("assignments", "0001_initial"),

        ("courses", "0001_initial"),

    ]


    operations = [

        migrations.AddField(

            model_name="assignment",

            name="course",

            field=models.ForeignKey(

                on_delete=django.db.models.deletion.CASCADE,

                related_name="assignments",

                to="courses.course",

            ),

        ),

        migrations.AddField(

            model_name="submission",

            name="assignment",

            field=models.ForeignKey(

                on_delete=django.db.models.deletion.CASCADE,

                related_name="submissions",

                to="assignments.assignment",

            ),

        ),

    ]
