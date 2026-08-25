from django.conf import settings

from django.db import migrations, models


class Migration(migrations.Migration):


    dependencies = [

        ('courses', '0007_alter_material_file_url'),

        migrations.swappable_dependency(settings.AUTH_USER_MODEL),

    ]


    operations = [

        migrations.AlterModelOptions(

            name='activitylog',

            options={'ordering': ['-created_at', 'id']},

        ),

        migrations.AlterModelOptions(

            name='announcement',

            options={'ordering': ['-created_at', 'id']},

        ),

        migrations.AlterModelOptions(

            name='course',

            options={'ordering': ['-created_at', 'id']},

        ),

        migrations.AlterModelOptions(

            name='material',

            options={'ordering': ['-uploaded_at', 'id']},

        ),

        migrations.AlterUniqueTogether(

            name='announcementread',

            unique_together=set(),

        ),

        migrations.AlterField(

            model_name='activitylog',

            name='action',

            field=models.CharField(db_index=True, max_length=100),

        ),

        migrations.AlterField(

            model_name='activitylog',

            name='created_at',

            field=models.DateTimeField(auto_now_add=True, db_index=True),

        ),

        migrations.AlterField(

            model_name='announcement',

            name='created_at',

            field=models.DateTimeField(auto_now_add=True, db_index=True),

        ),

        migrations.AlterField(

            model_name='course',

            name='category',

            field=models.CharField(db_index=True, max_length=100),

        ),

        migrations.AlterField(

            model_name='course',

            name='created_at',

            field=models.DateTimeField(auto_now_add=True, db_index=True),

        ),

        migrations.AlterField(

            model_name='course',

            name='status',

            field=models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')], db_index=True, default='draft', max_length=20),

        ),

        migrations.AddIndex(

            model_name='activitylog',

            index=models.Index(fields=['target_type', 'target_id'], name='courses_act_target__3a300d_idx'),

        ),

        migrations.AddConstraint(

            model_name='announcementread',

            constraint=models.UniqueConstraint(fields=('announcement', 'student'), name='unique_announcement_read'),

        ),

    ]
