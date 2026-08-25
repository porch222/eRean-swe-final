from django.db import migrations


class Migration(migrations.Migration):


    dependencies = [('courses', '0010_categories_to_majors')]


    operations = [

        migrations.RemoveField(model_name='course', name='category'),

    ]
