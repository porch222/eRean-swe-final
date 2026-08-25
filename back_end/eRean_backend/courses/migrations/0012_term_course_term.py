import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('courses', '0011_drop_course_category'),

    ]


    operations = [

        migrations.CreateModel(

            name='Term',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('code', models.CharField(help_text='e.g. 2026-FA', max_length=20, unique=True)),

                ('name', models.CharField(help_text='e.g. Fall 2026', max_length=100)),

                ('year', models.PositiveIntegerField()),

                ('starts_on', models.DateField()),

                ('ends_on', models.DateField()),

                ('is_current', models.BooleanField(default=False)),

            ],

            options={

                'ordering': ['-year', '-starts_on'],

                'constraints': [models.UniqueConstraint(condition=models.Q(('is_current', True)), fields=('is_current',), name='only_one_current_term'), models.CheckConstraint(condition=models.Q(('ends_on__gt', models.F('starts_on'))), name='term_ends_after_it_starts')],

            },

        ),

        migrations.AddField(

            model_name='course',

            name='term',

            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='courses', to='courses.term'),

        ),

    ]
