import courses.models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ("courses", "0006_announcementread"),

    ]


    operations = [

        migrations.AlterField(

            model_name="material",

            name="file_url",

            field=models.FileField(

                blank=True, null=True, upload_to=courses.models.material_upload_path

            ),

        ),

    ]
