from datetime import timedelta


from django.core.files.uploadedfile import SimpleUploadedFile

from django.urls import reverse

from django.utils import timezone

from rest_framework import status


from eRean_backend.testutils import BaseAPITestCase

from enrollments.models import Enrollment

from .models import (

    Assignment,

    QuizAnswer,

    QuizAttempt,

    QuizChoice,

    QuizQuestion,

    Submission,

)


def upload(name='answer.pdf'):

    return SimpleUploadedFile(name, b'%PDF-1.4 fake', content_type='application/pdf')


class AssignmentVisibilityTests(BaseAPITestCase):


    def setUp(self):

        super().setUp()

        self.make_assignment(course=self.course, title='Visible work')

        self.make_assignment(course=self.draft_course, title='Secret draft work')

        self.make_assignment(course=self.foreign_course, title='Other teacher work')


    def list_url(self, course):

        return reverse('assignment_list_create', kwargs={'course_pk': course.id})


    def test_enrolled_student_sees_the_coursework(self):

        self.as_user(self.student)

        response = self.client.get(self.list_url(self.course))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)


    def test_student_cannot_list_assignments_of_a_draft_course(self):

        self.as_user(self.student)

        response = self.client.get(self.list_url(self.draft_course))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_unenrolled_student_cannot_list_assignments(self):

        self.as_user(self.other_student)

        response = self.client.get(self.list_url(self.course))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_instructor_cannot_list_another_instructors_assignments(self):

        self.as_user(self.instructor)

        response = self.client.get(self.list_url(self.foreign_course))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_admin_can_list_any_courses_assignments(self):

        self.as_user(self.admin)

        response = self.client.get(self.list_url(self.draft_course))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AssignmentManagementTests(BaseAPITestCase):

    def test_instructor_creates_an_assignment(self):

        self.as_user(self.instructor)

        response = self.client.post(

            reverse('assignment_list_create', kwargs={'course_pk': self.course.id}),

            {

                'title': 'Essay',

                'description': 'Write it.',

                'type': 'assignment',

                'max_score': 50,

            },

        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_student_cannot_create_an_assignment(self):

        self.as_user(self.student)

        response = self.client.post(

            reverse('assignment_list_create', kwargs={'course_pk': self.course.id}),

            {'title': 'Nope', 'description': 'x', 'type': 'assignment'},

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_instructor_cannot_add_to_another_instructors_course(self):

        self.as_user(self.instructor)

        response = self.client.post(

            reverse('assignment_list_create', kwargs={'course_pk': self.foreign_course.id}),

            {'title': 'Nope', 'description': 'x', 'type': 'assignment'},

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AssignmentEditingTests(BaseAPITestCase):


    def setUp(self):

        super().setUp()

        self.assignment = Assignment.objects.create(

            course=self.course, title='Essay', description='Write it.',

            type=Assignment.ASSIGNMENT, max_score=100,

        )

        self.url = reverse(

            'assignment_detail',

            kwargs={'course_pk': self.course.id, 'pk': self.assignment.id},

        )


    def test_owner_can_correct_a_mistyped_assignment(self):

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {

            'title': 'Essay (revised)',

            'description': 'Write it properly.',

        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.title, 'Essay (revised)')


    def test_editing_keeps_existing_submissions(self):


        Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=80

        )

        self.as_user(self.instructor)

        self.client.patch(self.url, {'title': 'Essay v2'})

        self.assertEqual(self.assignment.submissions.count(), 1)


    def test_due_date_can_be_moved(self):

        self.as_user(self.instructor)

        later = (timezone.now() + timedelta(days=7)).isoformat()

        response = self.client.patch(self.url, {'due_date': later})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_moving_the_due_date_does_not_rewrite_lateness(self):


        submission = Submission.objects.create(

            assignment=self.assignment, student=self.student

        )

        submission.is_late = True

        submission.save(update_fields=['is_late'])


        self.as_user(self.instructor)

        self.client.patch(self.url, {

            'due_date': (timezone.now() + timedelta(days=30)).isoformat(),

        })

        submission.refresh_from_db()

        self.assertTrue(submission.is_late)


    def test_type_cannot_change_once_work_exists(self):

        Submission.objects.create(assignment=self.assignment, student=self.student)

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'type': 'quiz'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.type, Assignment.ASSIGNMENT)


    def test_type_can_change_while_nothing_depends_on_it(self):

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'type': 'quiz'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.type, Assignment.QUIZ)


    def test_maximum_cannot_drop_below_a_mark_already_given(self):


        Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=80

        )

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'max_score': 50})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.max_score, 100)


    def test_maximum_may_drop_when_it_still_covers_every_mark(self):

        Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=40

        )

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'max_score': 50})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_editing_does_not_disturb_progress(self):


        from enrollments.models import Enrollment


        Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=50

        )

        enrollment = Enrollment.objects.get(student=self.student, course=self.course)

        enrollment.progress = 100

        enrollment.save(update_fields=['progress'])


        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'max_score': 200, 'title': 'Renamed'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


        enrollment.refresh_from_db()

        self.assertEqual(enrollment.progress, 100)


    def test_a_raised_maximum_lowers_the_percentage_a_mark_is_worth(self):


        Submission.objects.create(

            assignment=self.assignment, student=self.student, grade=50

        )

        enrollment = Enrollment.objects.get(student=self.student, course=self.course)

        self.assertEqual(enrollment.compute_score(), 50)


        self.as_user(self.instructor)

        self.client.patch(self.url, {'max_score': 200})


        self.assertEqual(enrollment.compute_score(), 25)


    def test_instructor_cannot_edit_another_instructors_assignment(self):

        foreign = Assignment.objects.create(

            course=self.foreign_course, title='Theirs', description='x',

            type=Assignment.ASSIGNMENT, max_score=10,

        )

        url = reverse(

            'assignment_detail',

            kwargs={'course_pk': self.foreign_course.id, 'pk': foreign.id},

        )

        self.as_user(self.instructor)

        response = self.client.patch(url, {'title': 'Hijacked'})

        self.assertIn(

            response.status_code,

            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),

        )

        foreign.refresh_from_db()

        self.assertEqual(foreign.title, 'Theirs')


    def test_student_cannot_edit_an_assignment(self):

        self.as_user(self.student)

        response = self.client.patch(self.url, {'title': 'Mine now'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assignment.refresh_from_db()

        self.assertEqual(self.assignment.title, 'Essay')


class SubmissionTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.assignment = self.make_assignment()

        self.url = reverse(

            'submission_list_create',

            kwargs={'course_pk': self.course.id, 'assignment_pk': self.assignment.id},

        )


    def test_enrolled_student_can_submit(self):

        self.as_user(self.student)

        response = self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


        self.assertNotIn('file_url', response.data)


    def test_submitting_twice_creates_a_second_attempt(self):


        self.as_user(self.student)

        self.client.post(self.url, {'file_url': upload()}, format='multipart')

        second = self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

        self.assertEqual(second.data['attempt'], 2)


    def test_submission_requires_a_file(self):

        self.as_user(self.student)

        response = self.client.post(self.url, {}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_unsupported_file_type_is_rejected(self):

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'file_url': SimpleUploadedFile('a.exe', b'MZ', content_type='application/exe')},

            format='multipart',

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_unenrolled_student_cannot_submit(self):

        self.as_user(self.other_student)

        response = self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_submission_after_the_due_date_is_accepted_and_flagged(self):


        self.assignment.due_date = timezone.now() - timezone.timedelta(days=1)

        self.assignment.save()


        self.as_user(self.student)

        response = self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(response.data['is_late'])


    def test_file_submission_to_a_quiz_is_rejected(self):


        quiz = self.make_quiz()

        self.as_user(self.student)

        response = self.client.post(

            reverse(

                'submission_list_create',

                kwargs={'course_pk': self.course.id, 'assignment_pk': quiz.id},

            ),

            {'file_url': upload()},

            format='multipart',

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_student_sees_only_their_own_submission(self):

        Submission.objects.create(

            assignment=self.assignment, student=self.student, file_url=upload()

        )

        Enrollment.objects.create(student=self.other_student, course=self.course)

        Submission.objects.create(

            assignment=self.assignment, student=self.other_student, file_url=upload()

        )


        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertEqual(response.data['count'], 1)

        self.assertEqual(response.data['results'][0]['student'], self.student.id)


    def test_instructor_sees_every_submission(self):

        Submission.objects.create(

            assignment=self.assignment, student=self.student, file_url=upload()

        )

        self.as_user(self.instructor)

        response = self.client.get(self.url)

        self.assertEqual(response.data['count'], 1)


class GradingTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.assignment = self.make_assignment(max_score=100)

        self.submission = Submission.objects.create(

            assignment=self.assignment, student=self.student, file_url=upload()

        )

        self.url = reverse(

            'submission_detail',

            kwargs={

                'course_pk': self.course.id,

                'assignment_pk': self.assignment.id,

                'pk': self.submission.id,

            },

        )


    def test_instructor_grades_a_submission(self):

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'grade': 85, 'feedback': 'Nice work.'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


        self.assertEqual(response.data['student'], self.student.id)

        self.assertTrue(response.data['is_graded'])


        self.submission.refresh_from_db()

        self.assertEqual(float(self.submission.grade), 85)


    def test_grade_above_max_score_is_rejected(self):

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'grade': 150})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('grade', response.data)


    def test_negative_grade_is_rejected(self):

        self.as_user(self.instructor)

        response = self.client.patch(self.url, {'grade': -1})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_student_cannot_grade_themselves(self):

        self.as_user(self.student)

        response = self.client.patch(self.url, {'grade': 100})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_other_instructor_cannot_grade(self):

        self.as_user(self.other_instructor)

        response = self.client.patch(self.url, {'grade': 10})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_grading_updates_enrollment_progress(self):

        self.as_user(self.instructor)

        self.client.patch(self.url, {'grade': 70})


        self.enrollment.refresh_from_db()


        self.assertEqual(float(self.enrollment.progress), 100.0)


    def test_adding_an_assignment_recalculates_progress(self):


        self.as_user(self.instructor)

        self.client.patch(self.url, {'grade': 70})

        self.enrollment.refresh_from_db()

        self.assertEqual(float(self.enrollment.progress), 100.0)


        self.client.post(

            reverse('assignment_list_create', kwargs={'course_pk': self.course.id}),

            {'title': 'Second', 'description': 'x', 'type': 'assignment'},

        )

        self.enrollment.refresh_from_db()

        self.assertEqual(float(self.enrollment.progress), 50.0)


class SubmissionDownloadTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.assignment = self.make_assignment()

        self.submission = Submission.objects.create(

            assignment=self.assignment, student=self.student, file_url=upload()

        )

        self.url = reverse(

            'submission_download',

            kwargs={

                'course_pk': self.course.id,

                'assignment_pk': self.assignment.id,

                'pk': self.submission.id,

            },

        )


    def test_owner_can_download(self):

        self.as_user(self.student)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)


    def test_instructor_can_download(self):

        self.as_user(self.instructor)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)


    def test_another_student_cannot_download(self):

        self.as_user(self.other_student)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_404_NOT_FOUND)


class QuizChoiceDeletionTests(BaseAPITestCase):


    def setUp(self):

        super().setUp()

        self.quiz = self.make_quiz(max_score=10)

        self.question = QuizQuestion.objects.create(

            assignment=self.quiz, text='Pick one', points=10, order=0

        )

        self.choices = [

            QuizChoice.objects.create(

                question=self.question, text=f'Option {i}',

                is_correct=(i == 0), order=i,

            )

            for i in range(3)

        ]


    def url(self, choice):

        return reverse('quiz_choice_detail', kwargs={

            'course_pk': self.course.id,

            'assignment_pk': self.quiz.id,

            'question_pk': self.question.id,

            'pk': choice.id,

        })


    def test_instructor_removes_a_spare_choice(self):

        self.as_user(self.instructor)

        response = self.client.delete(self.url(self.choices[2]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(self.question.choices.count(), 2)


    def test_a_chosen_answer_cannot_be_removed(self):

        attempt = QuizAttempt.objects.create(

            assignment=self.quiz, student=self.student

        )

        QuizAnswer.objects.create(

            attempt=attempt, question=self.question,

            selected_choice=self.choices[2], is_correct=False,

        )


        self.as_user(self.instructor)

        response = self.client.delete(self.url(self.choices[2]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(QuizChoice.objects.filter(pk=self.choices[2].pk).exists())

        self.assertEqual(QuizAnswer.objects.count(), 1)


    def test_a_question_cannot_be_left_with_one_choice(self):

        self.as_user(self.instructor)

        self.client.delete(self.url(self.choices[2]))

        response = self.client.delete(self.url(self.choices[1]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(self.question.choices.count(), 2)


    def test_student_cannot_remove_a_choice(self):

        self.as_user(self.student)

        response = self.client.delete(self.url(self.choices[2]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_instructor_cannot_touch_another_courses_choice(self):

        foreign_quiz = Assignment.objects.create(

            course=self.foreign_course, title='Theirs', description='x',

            type=Assignment.QUIZ, max_score=10,

        )

        question = QuizQuestion.objects.create(

            assignment=foreign_quiz, text='q', points=10, order=0

        )

        choice = QuizChoice.objects.create(

            question=question, text='a', is_correct=True, order=0

        )

        self.as_user(self.instructor)

        response = self.client.delete(reverse('quiz_choice_detail', kwargs={

            'course_pk': self.foreign_course.id,

            'assignment_pk': foreign_quiz.id,

            'question_pk': question.id,

            'pk': choice.id,

        }))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(QuizChoice.objects.filter(pk=choice.pk).exists())


class QuizTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.quiz = self.make_quiz(max_score=30)

        self.questions = []

        for index in range(3):

            question = QuizQuestion.objects.create(

                assignment=self.quiz, text=f'Question {index}', points=10, order=index

            )

            QuizChoice.objects.create(question=question, text='right', is_correct=True, order=0)

            QuizChoice.objects.create(question=question, text='wrong', is_correct=False, order=1)

            self.questions.append(question)


        self.attempt_url = reverse(

            'quiz_attempt_list_create',

            kwargs={'course_pk': self.course.id, 'assignment_pk': self.quiz.id},

        )

        self.question_url = reverse(

            'quiz_question_list_create',

            kwargs={'course_pk': self.course.id, 'assignment_pk': self.quiz.id},

        )


    def answers(self, correct_count):


        payload = []

        for index, question in enumerate(self.questions):

            choice = question.choices.get(is_correct=index < correct_count)

            payload.append({'question': question.id, 'selected_choice': choice.id})

        return payload


    def test_student_does_not_see_which_choice_is_correct(self):

        self.as_user(self.student)

        response = self.client.get(self.question_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn('is_correct', str(response.data))


    def test_instructor_sees_which_choice_is_correct(self):

        self.as_user(self.instructor)

        response = self.client.get(self.question_url)

        self.assertIn('is_correct', response.data['results'][0]['choices'][0])


    def test_unenrolled_student_cannot_see_questions(self):

        self.as_user(self.other_student)

        self.assertEqual(

            self.client.get(self.question_url).status_code, status.HTTP_403_FORBIDDEN

        )


    def test_attempt_returns_the_score_and_per_answer_results(self):


        self.as_user(self.student)

        response = self.client.post(

            self.attempt_url, {'answers': self.answers(3)}, format='json'

        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(float(response.data['score']), 30.0)

        self.assertEqual(len(response.data['answers']), 3)

        self.assertTrue(all(a['is_correct'] for a in response.data['answers']))


    def test_partial_score_is_calculated(self):

        self.as_user(self.student)

        response = self.client.post(

            self.attempt_url, {'answers': self.answers(2)}, format='json'

        )

        self.assertEqual(float(response.data['score']), 20.0)


    def test_score_is_capped_at_the_max_score(self):

        self.quiz.max_score = 15

        self.quiz.save()


        self.as_user(self.student)

        response = self.client.post(

            self.attempt_url, {'answers': self.answers(3)}, format='json'

        )

        self.assertEqual(float(response.data['score']), 15.0)


    def test_quiz_attempt_creates_a_graded_submission(self):

        self.as_user(self.student)

        self.client.post(self.attempt_url, {'answers': self.answers(3)}, format='json')


        submission = Submission.objects.get(assignment=self.quiz, student=self.student)

        self.assertEqual(float(submission.grade), 30.0)


    def test_only_one_attempt_is_allowed(self):

        self.as_user(self.student)

        self.client.post(self.attempt_url, {'answers': self.answers(3)}, format='json')

        second = self.client.post(

            self.attempt_url, {'answers': self.answers(1)}, format='json'

        )

        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(QuizAttempt.objects.filter(assignment=self.quiz).count(), 1)


    def test_answering_the_same_question_twice_is_rejected(self):

        question = self.questions[0]

        payload = [

            {'question': question.id, 'selected_choice': question.choices.first().id},

            {'question': question.id, 'selected_choice': question.choices.last().id},

        ]

        self.as_user(self.student)

        response = self.client.post(self.attempt_url, {'answers': payload}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_a_choice_from_another_question_is_rejected(self):

        payload = [

            {

                'question': self.questions[0].id,

                'selected_choice': self.questions[1].choices.first().id,

            }

        ]

        self.as_user(self.student)

        response = self.client.post(self.attempt_url, {'answers': payload}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_unenrolled_student_cannot_attempt(self):

        self.as_user(self.other_student)

        response = self.client.post(

            self.attempt_url, {'answers': self.answers(3)}, format='json'

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_attempt_after_the_due_date_is_rejected(self):

        self.quiz.due_date = timezone.now() - timezone.timedelta(days=1)

        self.quiz.save()


        self.as_user(self.student)

        response = self.client.post(

            self.attempt_url, {'answers': self.answers(3)}, format='json'

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_instructor_cannot_attempt_a_quiz(self):

        self.as_user(self.instructor)

        response = self.client.post(

            self.attempt_url, {'answers': self.answers(3)}, format='json'

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_a_failed_attempt_leaves_no_partial_records(self):


        bad = [{'question': self.questions[0].id, 'selected_choice': 999999}]

        self.as_user(self.student)

        self.client.post(self.attempt_url, {'answers': bad}, format='json')


        self.assertFalse(QuizAttempt.objects.filter(assignment=self.quiz).exists())

        self.assertFalse(Submission.objects.filter(assignment=self.quiz).exists())


    def test_student_sees_only_their_own_attempts(self):

        Enrollment.objects.create(student=self.other_student, course=self.course)

        self.as_user(self.other_student)

        self.client.post(self.attempt_url, {'answers': self.answers(3)}, format='json')


        self.as_user(self.student)

        response = self.client.get(self.attempt_url)

        self.assertEqual(response.data['count'], 0)


    def test_instructor_sees_all_attempts(self):

        self.as_user(self.student)

        self.client.post(self.attempt_url, {'answers': self.answers(3)}, format='json')


        self.as_user(self.instructor)

        response = self.client.get(self.attempt_url)

        self.assertEqual(response.data['count'], 1)


class MySubmissionsTests(BaseAPITestCase):

    def test_student_sees_their_grades_across_courses(self):

        assignment = self.make_assignment()

        Submission.objects.create(

            assignment=assignment, student=self.student, file_url=upload(), grade=90

        )


        self.as_user(self.student)

        response = self.client.get(reverse('my_submissions'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)

        self.assertEqual(response.data['results'][0]['course_title'], self.course.title)

        self.assertEqual(response.data['results'][0]['assignment_title'], assignment.title)


    def test_instructor_cannot_use_the_student_grades_endpoint(self):

        self.as_user(self.instructor)

        response = self.client.get(reverse('my_submissions'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
