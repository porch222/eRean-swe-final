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

            name='AttendanceSession',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('date', models.DateField()),

                ('title', models.CharField(blank=True, default='', max_length=200)),

                ('created_at', models.DateTimeField(auto_now_add=True)),

                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_sessions', to='courses.course')),

            ],

            options={

                'ordering': ['-date', 'id'],

            },

        ),

        migrations.CreateModel(

            name='AttendanceRecord',

            fields=[

                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),

                ('status', models.CharField(choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late'), ('excused', 'Excused')], default='present', max_length=20)),

                ('note', models.CharField(blank=True, default='', max_length=200)),

                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to=settings.AUTH_USER_MODEL)),

                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='attendance.attendancesession')),

            ],

            options={

                'ordering': ['student__username', 'id'],

            },

        ),

        migrations.AddConstraint(

            model_name='attendancesession',

            constraint=models.UniqueConstraint(fields=('course', 'date'), name='one_attendance_session_per_day'),

        ),

        migrations.AddConstraint(

            model_name='attendancerecord',

            constraint=models.UniqueConstraint(fields=('session', 'student'), name='one_attendance_record_per_student'),

        ),

    ]
