import assignments.models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ("assignments", "0004_quiz_models"),

    ]


    operations = [

        migrations.AlterField(

            model_name="submission",

            name="file_url",

            field=models.FileField(

                blank=True,

                null=True,

                upload_to=assignments.models.submission_upload_path,

            ),

        ),

    ]
