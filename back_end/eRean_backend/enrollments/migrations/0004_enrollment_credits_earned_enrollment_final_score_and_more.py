import django.core.validators

import django.db.models.deletion

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('enrollments', '0003_alter_enrollment_options_and_more'),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.AddField(

            model_name='enrollment',

            name='credits_earned',

            field=models.PositiveSmallIntegerField(default=0),

        ),

        migrations.AddField(

            model_name='enrollment',

            name='final_score',

            field=models.DecimalField(blank=True, decimal_places=2, help_text='Percentage across all graded work, at the time of finalising.', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),

        ),

        migrations.AddField(

            model_name='enrollment',

            name='finalized_at',

            field=models.DateTimeField(blank=True, null=True),

        ),

        migrations.AddField(

            model_name='enrollment',

            name='letter_grade',

            field=models.CharField(blank=True, default='', max_length=2),

        ),

        migrations.CreateModel(

            name='DropRequest',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('reason', models.TextField(blank=True, default='')),

                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], db_index=True, default='pending', max_length=20)),

                ('decision_note', models.TextField(blank=True, default='')),

                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),

                ('decided_at', models.DateTimeField(blank=True, null=True)),

                ('decided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drop_decisions', to=settings.AUTH_USER_MODEL)),

                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drop_requests', to='enrollments.enrollment')),

            ],

            options={

                'ordering': ['-created_at', 'id'],

                'constraints': [models.UniqueConstraint(condition=models.Q(('status', 'pending')), fields=('enrollment',), name='one_pending_drop_request_per_enrollment')],

            },

        ),

    ]
