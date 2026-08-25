from django.urls import reverse


from eRean_backend.testutils import BaseAPITestCase

from assignments.models import Assignment, Submission

from .models import DropRequest, Enrollment, letter_for


class DropRequestTests(BaseAPITestCase):


    def test_student_cannot_set_their_own_status_to_dropped(self):

        self.as_user(self.student)

        response = self.client.patch(

            f'/api/enrollments/{self.enrollment.id}/', {'status': 'dropped'}

        )

        self.enrollment.refresh_from_db()


        self.assertEqual(self.enrollment.status, Enrollment.ACTIVE)


    def test_student_cannot_delete_their_enrollment(self):

        self.as_user(self.student)

        response = self.client.delete(f'/api/enrollments/{self.enrollment.id}/')

        self.assertEqual(response.status_code, 403)

        self.assertTrue(Enrollment.objects.filter(pk=self.enrollment.pk).exists())


    def test_student_raises_a_drop_request(self):

        self.as_user(self.student)

        response = self.client.post(

            '/api/enrollments/drop-requests/',

            {'enrollment': self.enrollment.id, 'reason': 'Clashes with work.'},

        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.data['status'], DropRequest.PENDING)

        self.enrollment.refresh_from_db()

        self.assertEqual(self.enrollment.status, Enrollment.ACTIVE)


    def test_only_one_pending_request_at_a_time(self):

        self.as_user(self.student)

        payload = {'enrollment': self.enrollment.id}

        self.client.post('/api/enrollments/drop-requests/', payload)

        second = self.client.post('/api/enrollments/drop-requests/', payload)

        self.assertEqual(second.status_code, 400)


    def test_student_cannot_request_a_drop_for_someone_else(self):

        other = Enrollment.objects.create(

            student=self.other_student, course=self.course

        )

        self.as_user(self.student)

        response = self.client.post(

            '/api/enrollments/drop-requests/', {'enrollment': other.id}

        )

        self.assertEqual(response.status_code, 400)


    def test_instructor_approval_drops_the_course(self):

        drop = DropRequest.objects.create(enrollment=self.enrollment)

        self.as_user(self.instructor)

        response = self.client.post(

            f'/api/enrollments/drop-requests/{drop.id}/decide/',

            {'status': DropRequest.APPROVED, 'decision_note': 'Approved.'},

        )

        self.assertEqual(response.status_code, 200)

        self.enrollment.refresh_from_db()

        self.assertEqual(self.enrollment.status, Enrollment.DROPPED)


    def test_rejection_leaves_the_enrollment_active(self):

        drop = DropRequest.objects.create(enrollment=self.enrollment)

        self.as_user(self.instructor)

        self.client.post(

            f'/api/enrollments/drop-requests/{drop.id}/decide/',

            {'status': DropRequest.REJECTED},

        )

        self.enrollment.refresh_from_db()

        self.assertEqual(self.enrollment.status, Enrollment.ACTIVE)


    def test_student_cannot_decide_their_own_request(self):

        drop = DropRequest.objects.create(enrollment=self.enrollment)

        self.as_user(self.student)

        response = self.client.post(

            f'/api/enrollments/drop-requests/{drop.id}/decide/',

            {'status': DropRequest.APPROVED},

        )

        self.assertEqual(response.status_code, 403)

        self.enrollment.refresh_from_db()

        self.assertEqual(self.enrollment.status, Enrollment.ACTIVE)


    def test_an_unrelated_instructor_cannot_decide(self):

        drop = DropRequest.objects.create(enrollment=self.enrollment)

        self.as_user(self.other_instructor)

        response = self.client.post(

            f'/api/enrollments/drop-requests/{drop.id}/decide/',

            {'status': DropRequest.APPROVED},

        )

        self.assertEqual(response.status_code, 403)


    def test_a_decided_request_cannot_be_decided_again(self):

        drop = DropRequest.objects.create(enrollment=self.enrollment)

        self.as_user(self.instructor)

        url = f'/api/enrollments/drop-requests/{drop.id}/decide/'

        self.client.post(url, {'status': DropRequest.REJECTED})

        again = self.client.post(url, {'status': DropRequest.APPROVED})

        self.assertEqual(again.status_code, 400)


    def test_students_only_see_their_own_requests(self):

        DropRequest.objects.create(enrollment=self.enrollment)

        other = Enrollment.objects.create(student=self.other_student, course=self.course)

        DropRequest.objects.create(enrollment=other)


        self.as_user(self.student)

        response = self.client.get('/api/enrollments/drop-requests/')

        ids = {row['enrollment'] for row in response.data['results']}

        self.assertEqual(ids, {self.enrollment.id})


class FinalGradeTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.assignment = Assignment.objects.create(

            course=self.course, title='Essay', description='x', max_score=100

        )


    def test_letter_bands(self):

        self.assertEqual(letter_for(95), 'A')

        self.assertEqual(letter_for(83), 'B')

        self.assertEqual(letter_for(60), 'D-')

        self.assertEqual(letter_for(12), 'F')

        self.assertEqual(letter_for(None), '')


    def test_finalizing_freezes_score_letter_and_credits(self):

        Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=90

        )

        self.as_user(self.instructor)

        response = self.client.post(f'/api/enrollments/{self.enrollment.id}/finalize/')

        self.assertEqual(response.status_code, 200)


        self.enrollment.refresh_from_db()

        self.assertEqual(float(self.enrollment.final_score), 90.0)

        self.assertEqual(self.enrollment.letter_grade, 'A-')

        self.assertEqual(self.enrollment.credits_earned, self.course.credits)

        self.assertEqual(self.enrollment.status, Enrollment.COMPLETED)

        self.assertTrue(self.enrollment.is_passed)


    def test_a_failing_grade_earns_no_credits(self):

        Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=20

        )

        self.as_user(self.instructor)

        self.client.post(f'/api/enrollments/{self.enrollment.id}/finalize/')


        self.enrollment.refresh_from_db()

        self.assertEqual(self.enrollment.letter_grade, 'F')

        self.assertEqual(self.enrollment.credits_earned, 0)

        self.assertFalse(self.enrollment.is_passed)


    def test_a_later_grade_change_does_not_rewrite_a_final_grade(self):


        submission = Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=90

        )

        self.as_user(self.instructor)

        self.client.post(f'/api/enrollments/{self.enrollment.id}/finalize/')


        submission.grade = 10

        submission.save()


        self.enrollment.refresh_from_db()

        self.assertEqual(float(self.enrollment.final_score), 90.0)


    def test_students_cannot_finalize(self):

        self.as_user(self.student)

        response = self.client.post(f'/api/enrollments/{self.enrollment.id}/finalize/')

        self.assertEqual(response.status_code, 403)


    def test_a_course_with_no_assignments_has_no_score(self):

        empty = Enrollment.objects.create(

            student=self.other_student, course=self.foreign_course

        )

        self.assertIsNone(empty.compute_score())


class TranscriptTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        assignment = Assignment.objects.create(

            course=self.course, title='Essay', description='x', max_score=100

        )

        Submission.objects.create(assignment=assignment, student=self.student, grade=90)

        self.enrollment.finalize()


    def test_student_sees_their_own_transcript(self):

        self.as_user(self.student)

        response = self.client.get('/api/enrollments/transcript/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['credits_earned'], self.course.credits)

        self.assertEqual(response.data['gpa'], 3.7)


    def test_a_student_cannot_read_another_students_transcript(self):

        self.as_user(self.student)

        response = self.client.get(

            f'/api/enrollments/transcript/?student={self.other_student.id}'

        )

        self.assertEqual(response.status_code, 403)


    def test_staff_can_read_a_students_transcript(self):

        self.as_user(self.admin)

        response = self.client.get(

            f'/api/enrollments/transcript/?student={self.student.id}'

        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['student'], self.student.id)


    def test_dropped_courses_appear_but_earn_nothing(self):

        dropped = Enrollment.objects.create(

            student=self.student, course=self.foreign_course, status=Enrollment.DROPPED

        )

        self.as_user(self.student)

        response = self.client.get('/api/enrollments/transcript/')

        entry = next(

            r for r in response.data['entries'] if r['course'] == self.foreign_course.id

        )

        self.assertEqual(entry['status'], Enrollment.DROPPED)

        self.assertEqual(response.data['credits_earned'], self.course.credits)


class GradebookTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.a1 = Assignment.objects.create(

            course=self.course, title='One', description='x', max_score=50

        )

        self.a2 = Assignment.objects.create(

            course=self.course, title='Two', description='x', max_score=50

        )

        Submission.objects.create(assignment=self.a1, student=self.student, grade=40)


    def test_instructor_sees_every_student_against_every_assignment(self):

        self.as_user(self.instructor)

        response = self.client.get(f'/api/courses/{self.course.id}/gradebook/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data['assignments']), 2)

        self.assertEqual(response.data['points_possible'], 100)


        row = response.data['students'][0]

        self.assertEqual(row['total'], 40.0)

        self.assertEqual(row['percent'], 40.0)


        self.assertEqual(len(row['cells']), 2)

        self.assertFalse(row['cells'][1]['submitted'])


    def test_students_cannot_open_the_gradebook(self):

        self.as_user(self.student)

        response = self.client.get(f'/api/courses/{self.course.id}/gradebook/')

        self.assertEqual(response.status_code, 403)


    def test_an_unrelated_instructor_cannot_open_it(self):

        self.as_user(self.other_instructor)

        response = self.client.get(f'/api/courses/{self.course.id}/gradebook/')

        self.assertEqual(response.status_code, 403)


class ResubmissionAccountingTests(BaseAPITestCase):


    def setUp(self):

        super().setUp()

        self.a1 = Assignment.objects.create(

            course=self.course, title='One', description='x', max_score=100

        )

        self.a2 = Assignment.objects.create(

            course=self.course, title='Two', description='x', max_score=100

        )


    def graded_attempts(self, assignment, *grades):


        for grade in grades:

            Submission.objects.create(

                assignment=assignment, student=self.student, grade=grade

            )


    def test_only_the_latest_attempt_counts_toward_the_score(self):

        self.graded_attempts(self.a1, 40, 90)


        self.assertEqual(self.enrollment.compute_score(), 45.0)


    def test_a_resubmitted_assignment_cannot_push_the_score_over_100(self):

        self.graded_attempts(self.a1, 100, 100)

        self.graded_attempts(self.a2, 100, 100)

        score = self.enrollment.compute_score()

        self.assertLessEqual(score, 100.0)

        self.assertEqual(score, 100.0)


    def test_progress_counts_assignments_not_attempts(self):

        from assignments.views import update_enrollment_progress


        self.graded_attempts(self.a1, 50, 60)

        update_enrollment_progress(self.student, self.course)

        self.enrollment.refresh_from_db()


        self.assertEqual(float(self.enrollment.progress), 50.0)


class StudentParamTests(BaseAPITestCase):


    def test_non_numeric_student_id_is_a_bad_request(self):

        self.as_user(self.admin)

        response = self.client.get('/api/enrollments/transcript/?student=abc')

        self.assertEqual(response.status_code, 400)


    def test_non_numeric_student_id_is_a_bad_request_for_students_too(self):

        self.as_user(self.student)

        response = self.client.get('/api/enrollments/transcript/?student=%27%20OR%201=1')

        self.assertEqual(response.status_code, 400)
