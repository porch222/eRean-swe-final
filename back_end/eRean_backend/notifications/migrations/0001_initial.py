import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):


    initial = True


    dependencies = [

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.CreateModel(

            name='Notification',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('kind', models.CharField(choices=[('grade', 'Grade posted'), ('assignment', 'New coursework'), ('announcement', 'Announcement'), ('reply', 'Discussion reply'), ('drop_request', 'Drop request'), ('drop_decision', 'Drop decision'), ('attendance', 'Attendance')], db_index=True, max_length=30)),

                ('message', models.CharField(max_length=300)),

                ('link_url', models.CharField(blank=True, default='', max_length=300)),

                ('is_read', models.BooleanField(db_index=True, default=False)),

                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),

                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),

            ],

            options={

                'ordering': ['-created_at', 'id'],

                'indexes': [models.Index(fields=['recipient', 'is_read'], name='notificatio_recipie_4e3567_idx')],

            },

        ),

    ]
