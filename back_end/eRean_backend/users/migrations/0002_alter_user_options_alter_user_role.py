from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('users', '0001_initial'),

    ]


    operations = [

        migrations.AlterModelOptions(

            name='user',

            options={'ordering': ['username']},

        ),

        migrations.AlterField(

            model_name='user',

            name='role',

            field=models.CharField(choices=[('admin', 'Admin'), ('instructor', 'Instructor'), ('student', 'Student')], db_index=True, default='student', max_length=20),

        ),

    ]
