from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [

        ("courses", "0002_initial"),

    ]


    operations = [

        migrations.AddField(

            model_name="material",

            name="link_url",

            field=models.URLField(blank=True, max_length=500, null=True),

        ),

        migrations.AlterField(

            model_name="material",

            name="file_url",

            field=models.FileField(blank=True, null=True, upload_to="materials/"),

        ),

    ]
