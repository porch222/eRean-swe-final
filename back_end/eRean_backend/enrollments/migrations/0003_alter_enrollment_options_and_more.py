import django.core.validators

from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('courses', '0008_alter_activitylog_options_alter_announcement_options_and_more'),

        ('enrollments', '0002_initial'),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.AlterModelOptions(

            name='enrollment',

            options={'ordering': ['-enrolled_at', 'id']},

        ),

        migrations.AlterUniqueTogether(

            name='enrollment',

            unique_together=set(),

        ),

        migrations.AlterField(

            model_name='enrollment',

            name='progress',

            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),

        ),

        migrations.AddConstraint(

            model_name='enrollment',

            constraint=models.UniqueConstraint(fields=('student', 'course'), name='unique_student_course_enrollment'),

        ),

    ]
