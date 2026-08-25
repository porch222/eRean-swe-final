import django.core.validators

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('assignments', '0005_alter_submission_file_url'),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.AlterModelOptions(

            name='assignment',

            options={'ordering': ['-created_at', 'id']},

        ),

        migrations.AlterModelOptions(

            name='quizanswer',

            options={'ordering': ['question__order', 'id']},

        ),

        migrations.AlterModelOptions(

            name='quizattempt',

            options={'ordering': ['-submitted_at', 'id']},

        ),

        migrations.AlterModelOptions(

            name='quizchoice',

            options={'ordering': ['order', 'id']},

        ),

        migrations.AlterModelOptions(

            name='quizquestion',

            options={'ordering': ['order', 'id']},

        ),

        migrations.AlterModelOptions(

            name='submission',

            options={'ordering': ['-submitted_at', 'id']},

        ),

        migrations.AlterUniqueTogether(

            name='quizanswer',

            unique_together=set(),

        ),

        migrations.AlterUniqueTogether(

            name='quizattempt',

            unique_together=set(),

        ),

        migrations.AlterUniqueTogether(

            name='submission',

            unique_together=set(),

        ),

        migrations.AlterField(

            model_name='assignment',

            name='max_score',

            field=models.PositiveIntegerField(default=100, validators=[django.core.validators.MinValueValidator(1)]),

        ),

        migrations.AlterField(

            model_name='submission',

            name='feedback',

            field=models.TextField(blank=True, default=''),

        ),

        migrations.AddConstraint(

            model_name='quizanswer',

            constraint=models.UniqueConstraint(fields=('attempt', 'question'), name='unique_answer_per_question'),

        ),

        migrations.AddConstraint(

            model_name='quizattempt',

            constraint=models.UniqueConstraint(fields=('assignment', 'student'), name='unique_quiz_attempt'),

        ),

        migrations.AddConstraint(

            model_name='submission',

            constraint=models.UniqueConstraint(fields=('assignment', 'student'), name='unique_assignment_submission'),

        ),

    ]
