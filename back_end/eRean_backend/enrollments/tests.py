from django.urls import reverse

from rest_framework import status

from rest_framework.test import APITestCase

from users.models import User

from courses.models import Course, Major

from .models import Enrollment


class EnrollmentTests(APITestCase):


    def setUp(self):

        self.instructor = User.objects.create_user(

            username='inst1', password='pass1234', role='instructor'

        )

        self.instructor2 = User.objects.create_user(

            username='inst2', password='pass1234', role='instructor'

        )

        self.student1 = User.objects.create_user(

            username='student1', password='pass1234', role='student'

        )

        self.student2 = User.objects.create_user(

            username='student2', password='pass1234', role='student'

        )


        self.major_cs = Major.objects.create(code='CS', name='Computer Science')


        self.course1 = Course.objects.create(

            title='Course 1', description='Desc', major=self.major_cs, instructor=self.instructor, status='published'

        )

        self.course2 = Course.objects.create(

            title='Course 2', description='Desc', major=self.major_cs, instructor=self.instructor2, status='published'

        )


        self.enrollment_list_url = reverse('enrollment_list_create')


    def test_student_enrollment_success(self):

        self.client.force_authenticate(user=self.student1)

        data = {'course': self.course1.id}

        response = self.client.post(self.enrollment_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data['student'], self.student1.id)


    def test_student_enrollment_duplicate(self):

        self.client.force_authenticate(user=self.student1)


        Enrollment.objects.create(student=self.student1, course=self.course1)


        data = {'course': self.course1.id}

        response = self.client.post(self.enrollment_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_instructor_cannot_enroll(self):

        self.client.force_authenticate(user=self.instructor)

        data = {'course': self.course1.id}

        response = self.client.post(self.enrollment_list_url, data)


        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_enrollment_visibility(self):


        Enrollment.objects.create(student=self.student1, course=self.course1)

        Enrollment.objects.create(student=self.student2, course=self.course1)

        Enrollment.objects.create(student=self.student1, course=self.course2)


        self.client.force_authenticate(user=self.student1)

        response = self.client.get(self.enrollment_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 2)


        self.client.force_authenticate(user=self.instructor)

        response = self.client.get(self.enrollment_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 2)

        course_ids = [e['course'] for e in response.data['results']]

        self.assertTrue(all(c == self.course1.id for c in course_ids))


    def test_student_cannot_modify_progress_directly(self):

        enrollment = Enrollment.objects.create(student=self.student1, course=self.course1)

        self.client.force_authenticate(user=self.student1)


        detail_url = reverse('enrollment_detail', kwargs={'pk': enrollment.id})

        data = {'progress': 50.0}


        response = self.client.patch(detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


        enrollment.refresh_from_db()

        self.assertEqual(enrollment.progress, 0.0)
