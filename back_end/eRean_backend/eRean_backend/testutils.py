import shutil

import tempfile


from django.contrib.auth import get_user_model

from django.test import override_settings

from django.utils import timezone

from rest_framework.test import APITestCase


from assignments.models import Assignment

from courses.models import Course, Major

from enrollments.models import Enrollment


User = get_user_model()


PASSWORD = 'TestPass!2026'


def make_user(username, role, **extra):

    return User.objects.create_user(

        username=username,

        email=f'{username}@test.local',

        password=PASSWORD,

        role=role,

        **extra,

    )


_TEMP_MEDIA = tempfile.mkdtemp(prefix='erean-test-media-')


@override_settings(MEDIA_ROOT=_TEMP_MEDIA)

class BaseAPITestCase(APITestCase):

    @classmethod

    def tearDownClass(cls):

        shutil.rmtree(_TEMP_MEDIA, ignore_errors=True)

        super().tearDownClass()


    def setUp(self):

        self.admin = make_user('admin1', User.ADMIN)

        self.instructor = make_user('teacher1', User.INSTRUCTOR)

        self.other_instructor = make_user('teacher2', User.INSTRUCTOR)

        self.student = make_user('student1', User.STUDENT)

        self.other_student = make_user('student2', User.STUDENT)


        self.major_cs = Major.objects.create(code='CS', name='Computer Science')

        self.major_math = Major.objects.create(code='MATH', name='Mathematics')


        self.course = Course.objects.create(

            title='Published Course',

            description='A course students can see.',

            major=self.major_cs,

            instructor=self.instructor,

            status=Course.PUBLISHED,

        )

        self.draft_course = Course.objects.create(

            title='Draft Course',

            description='Not approved yet.',

            major=self.major_cs,

            instructor=self.instructor,

            status=Course.DRAFT,

        )

        self.foreign_course = Course.objects.create(

            title='Another Instructor Course',

            description='Owned by teacher2.',

            major=self.major_math,

            instructor=self.other_instructor,

            status=Course.PUBLISHED,

        )


        self.enrollment = Enrollment.objects.create(

            student=self.student, course=self.course

        )


    def as_user(self, user):

        self.client.force_authenticate(user=user)


    def make_assignment(self, course=None, **extra):

        defaults = {

            'title': 'Assignment 1',

            'description': 'Do the thing.',

            'type': Assignment.ASSIGNMENT,

            'due_date': timezone.now() + timezone.timedelta(days=7),

            'max_score': 100,

        }

        defaults.update(extra)

        return Assignment.objects.create(course=course or self.course, **defaults)


    def make_quiz(self, course=None, **extra):

        return self.make_assignment(course=course, type=Assignment.QUIZ, **extra)
