from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('courses', '0012_term_course_term'),

    ]


    operations = [

        migrations.AddField(

            model_name='announcement',

            name='edited_at',

            field=models.DateTimeField(blank=True, null=True),

        ),

        migrations.AddField(

            model_name='curriculum',

            name='credits_to_graduate',

            field=models.PositiveIntegerField(blank=True, help_text='Total credits needed for the degree, electives included. Leave blank to require exactly the required courses and nothing more.', null=True),

        ),

    ]
