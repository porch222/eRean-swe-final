import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):


    initial = True


    dependencies = [

        ('courses', '0011_drop_course_category'),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.CreateModel(

            name='Thread',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('kind', models.CharField(choices=[('discussion', 'Discussion'), ('question', 'Question')], db_index=True, default='discussion', max_length=20)),

                ('title', models.CharField(max_length=200)),

                ('body', models.TextField()),

                ('is_pinned', models.BooleanField(default=False)),

                ('is_locked', models.BooleanField(default=False)),

                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),

                ('updated_at', models.DateTimeField(auto_now=True)),

                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='threads', to=settings.AUTH_USER_MODEL)),

                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='threads', to='courses.course')),

            ],

            options={

                'ordering': ['-is_pinned', '-created_at', 'id'],

            },

        ),

        migrations.CreateModel(

            name='Reply',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('body', models.TextField()),

                ('is_answer', models.BooleanField(default=False)),

                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),

                ('updated_at', models.DateTimeField(auto_now=True)),

                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to=settings.AUTH_USER_MODEL)),

                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='discussions.thread')),

            ],

            options={

                'ordering': ['created_at', 'id'],

                'constraints': [models.UniqueConstraint(condition=models.Q(('is_answer', True)), fields=('thread',), name='one_accepted_answer_per_thread')],

            },

        ),

    ]
