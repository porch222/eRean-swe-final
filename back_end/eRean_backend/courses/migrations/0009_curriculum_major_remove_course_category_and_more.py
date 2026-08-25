import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('courses', '0008_alter_activitylog_options_alter_announcement_options_and_more'),

    ]


    operations = [

        migrations.CreateModel(

            name='Curriculum',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('name', models.CharField(max_length=120)),

                ('year', models.PositiveIntegerField(help_text='Intake year this version applies to.')),

                ('is_active', models.BooleanField(db_index=True, default=True)),

            ],

            options={

                'ordering': ['major__name', '-year'],

            },

        ),

        migrations.CreateModel(

            name='Major',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('code', models.CharField(max_length=20, unique=True)),

                ('name', models.CharField(max_length=120, unique=True)),

                ('description', models.TextField(blank=True)),

            ],

            options={

                'ordering': ['name'],

            },

        ),

        migrations.AddField(

            model_name='course',

            name='credits',

            field=models.PositiveSmallIntegerField(default=3),

        ),

        migrations.CreateModel(

            name='CurriculumCourse',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('year_level', models.PositiveSmallIntegerField(default=1)),

                ('term', models.PositiveSmallIntegerField(default=1)),

                ('is_required', models.BooleanField(default=True)),

                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curriculum_entries', to='courses.course')),

                ('curriculum', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='courses.curriculum')),

            ],

            options={

                'ordering': ['year_level', 'term', 'course__title'],

            },

        ),

        migrations.AddField(

            model_name='curriculum',

            name='courses',

            field=models.ManyToManyField(related_name='curricula', through='courses.CurriculumCourse', to='courses.course'),

        ),

        migrations.AddField(

            model_name='curriculum',

            name='major',

            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curricula', to='courses.major'),

        ),

        migrations.AddField(

            model_name='course',

            name='major',

            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='courses', to='courses.major'),

        ),

        migrations.AddConstraint(

            model_name='curriculumcourse',

            constraint=models.UniqueConstraint(fields=('curriculum', 'course'), name='unique_course_per_curriculum'),

        ),

        migrations.AddConstraint(

            model_name='curriculum',

            constraint=models.UniqueConstraint(fields=('major', 'year'), name='unique_major_curriculum_year'),

        ),

    ]
