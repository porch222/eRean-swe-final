from datetime import date


from eRean_backend.testutils import BaseAPITestCase

from .models import AttendanceRecord, AttendanceSession


class AttendanceTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.base = f'/api/courses/{self.course.id}/attendance/'

        self.session = AttendanceSession.objects.create(

            course=self.course, date=date(2026, 3, 2), title='Week 1'

        )


    def test_instructor_creates_a_session(self):

        self.as_user(self.instructor)

        response = self.client.post(self.base, {'date': '2026-03-09', 'title': 'Week 2'})

        self.assertEqual(response.status_code, 201)


    def test_students_cannot_create_a_session(self):

        self.as_user(self.student)

        response = self.client.post(self.base, {'date': '2026-03-09'})

        self.assertEqual(response.status_code, 403)


    def test_enrolled_students_can_read_the_register(self):

        self.as_user(self.student)

        response = self.client.get(self.base)

        self.assertEqual(response.status_code, 200)


    def test_one_session_per_course_per_day(self):

        self.as_user(self.instructor)

        response = self.client.post(self.base, {'date': '2026-03-02'})

        self.assertEqual(response.status_code, 400)


    def test_marking_the_roster_in_one_request(self):

        self.as_user(self.instructor)

        response = self.client.post(

            f'{self.base}{self.session.id}/mark/',

            {'records': [{'student': self.student.id, 'status': 'present'}]},

            format='json',

        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(

            AttendanceRecord.objects.get(session=self.session).status, 'present'

        )


    def test_marking_again_updates_rather_than_duplicates(self):

        self.as_user(self.instructor)

        url = f'{self.base}{self.session.id}/mark/'

        self.client.post(

            url, {'records': [{'student': self.student.id, 'status': 'absent'}]},

            format='json',

        )

        self.client.post(

            url, {'records': [{'student': self.student.id, 'status': 'present'}]},

            format='json',

        )

        records = AttendanceRecord.objects.filter(session=self.session)

        self.assertEqual(records.count(), 1)

        self.assertEqual(records.first().status, 'present')


    def test_a_student_not_enrolled_cannot_be_marked(self):


        self.as_user(self.instructor)

        self.client.post(

            f'{self.base}{self.session.id}/mark/',

            {'records': [{'student': self.other_student.id, 'status': 'present'}]},

            format='json',

        )

        self.assertFalse(

            AttendanceRecord.objects.filter(student=self.other_student).exists()

        )


    def test_an_invalid_status_is_rejected(self):

        self.as_user(self.instructor)

        response = self.client.post(

            f'{self.base}{self.session.id}/mark/',

            {'records': [{'student': self.student.id, 'status': 'teleported'}]},

            format='json',

        )

        self.assertEqual(response.status_code, 400)


    def test_students_cannot_mark_attendance(self):

        self.as_user(self.student)

        response = self.client.post(

            f'{self.base}{self.session.id}/mark/',

            {'records': [{'student': self.student.id, 'status': 'present'}]},

            format='json',

        )

        self.assertEqual(response.status_code, 403)


    def test_a_student_sees_their_own_rate(self):

        AttendanceRecord.objects.create(

            session=self.session, student=self.student, status='present'

        )

        self.as_user(self.student)

        response = self.client.get(f'{self.base}me/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['attendance_rate'], 100.0)


    def test_late_still_counts_as_attended(self):

        AttendanceRecord.objects.create(

            session=self.session, student=self.student, status='late'

        )

        self.as_user(self.student)

        response = self.client.get(f'{self.base}me/')

        self.assertEqual(response.data['attended'], 1)


    def test_absence_counts_against_the_rate(self):

        AttendanceRecord.objects.create(

            session=self.session, student=self.student, status='absent'

        )

        self.as_user(self.student)

        response = self.client.get(f'{self.base}me/')

        self.assertEqual(response.data['attendance_rate'], 0.0)


    def test_a_student_cannot_read_another_students_attendance(self):


        self.as_user(self.student)

        response = self.client.get(f'{self.base}me/?student={self.other_student.id}')

        self.assertEqual(response.status_code, 403)


    def test_a_non_numeric_student_id_is_a_bad_request(self):

        self.as_user(self.instructor)

        response = self.client.get(f'{self.base}me/?student=abc')

        self.assertEqual(response.status_code, 400)


    def test_summary_is_staff_only(self):

        self.as_user(self.student)

        self.assertEqual(self.client.get(f'{self.base}summary/').status_code, 403)

        self.as_user(self.instructor)

        self.assertEqual(self.client.get(f'{self.base}summary/').status_code, 200)
