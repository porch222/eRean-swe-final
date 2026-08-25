from django.db import migrations


def categories_to_majors(apps, schema_editor):


    Course = apps.get_model('courses', 'Course')

    Major = apps.get_model('courses', 'Major')


    taken = set()

    for name in sorted({c for c in Course.objects.values_list('category', flat=True) if c}):

        base = ''.join(word[0] for word in name.split() if word).upper()[:20] or 'GEN'

        code, n = base, 2

        while code in taken:

            code = f'{base}{n}'

            n += 1

        taken.add(code)

        major, _ = Major.objects.get_or_create(name=name, defaults={'code': code})

        Course.objects.filter(category=name).update(major=major)


def majors_to_categories(apps, schema_editor):


    Course = apps.get_model('courses', 'Course')

    for course in Course.objects.select_related('major'):

        if course.major_id:

            course.category = course.major.name

            course.save(update_fields=['category'])


class Migration(migrations.Migration):


    dependencies = [('courses', '0009_curriculum_major_remove_course_category_and_more')]


    operations = [

        migrations.RunPython(categories_to_majors, majors_to_categories),

    ]
