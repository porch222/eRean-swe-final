import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('courses', '0009_curriculum_major_remove_course_category_and_more'),

        ('users', '0002_alter_user_options_alter_user_role'),

    ]


    operations = [

        migrations.AddField(

            model_name='user',

            name='major',

            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='courses.major'),

        ),

    ]
