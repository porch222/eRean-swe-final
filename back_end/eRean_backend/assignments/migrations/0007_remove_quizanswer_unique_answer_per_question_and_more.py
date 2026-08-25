import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('assignments', '0006_alter_assignment_options_alter_quizanswer_options_and_more'),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.RemoveConstraint(

            model_name='quizanswer',

            name='unique_answer_per_question',

        ),

        migrations.RemoveConstraint(

            model_name='submission',

            name='unique_assignment_submission',

        ),

        migrations.AddField(

            model_name='quizanswer',

            name='awarded_points',

            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),

        ),

        migrations.AddField(

            model_name='quizanswer',

            name='text_answer',

            field=models.TextField(blank=True, default=''),

        ),

        migrations.AddField(

            model_name='quizattempt',

            name='graded_at',

            field=models.DateTimeField(blank=True, null=True),

        ),

        migrations.AddField(

            model_name='quizattempt',

            name='needs_manual_grading',

            field=models.BooleanField(db_index=True, default=False),

        ),

        migrations.AddField(

            model_name='quizquestion',

            name='type',

            field=models.CharField(choices=[('single', 'Multiple choice (one answer)'), ('multiple', 'Multiple choice (several answers)'), ('true_false', 'True or false'), ('written', 'Written answer')], default='single', max_length=20),

        ),

        migrations.AddField(

            model_name='submission',

            name='attempt',

            field=models.PositiveSmallIntegerField(default=1),

        ),

        migrations.AddField(

            model_name='submission',

            name='is_late',

            field=models.BooleanField(default=False),

        ),

        migrations.AddField(

            model_name='submission',

            name='is_latest',

            field=models.BooleanField(db_index=True, default=True),

        ),

        migrations.AlterField(

            model_name='quizanswer',

            name='selected_choice',

            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='assignments.quizchoice'),

        ),

        migrations.AddConstraint(

            model_name='quizanswer',

            constraint=models.UniqueConstraint(fields=('attempt', 'question', 'selected_choice'), name='unique_answer_per_question_choice'),

        ),

        migrations.AddConstraint(

            model_name='submission',

            constraint=models.UniqueConstraint(fields=('assignment', 'student', 'attempt'), name='unique_assignment_submission_attempt'),

        ),

    ]
