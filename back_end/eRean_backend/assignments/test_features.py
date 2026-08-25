from datetime import timedelta


from django.core.files.uploadedfile import SimpleUploadedFile

from django.utils import timezone


from eRean_backend.testutils import BaseAPITestCase

from .models import (

    Assignment,

    QuizAnswer,

    QuizAttempt,

    QuizChoice,

    QuizQuestion,

    Submission,

)


def upload(name='work.pdf'):

    return SimpleUploadedFile(name, b'%PDF-1.4 fake', content_type='application/pdf')


class ResubmissionTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.assignment = Assignment.objects.create(

            course=self.course, title='Essay', description='x', max_score=100,

            due_date=timezone.now() + timedelta(days=7),

        )

        self.url = (

            f'/api/courses/{self.course.id}/assignments/{self.assignment.id}/submissions/'

        )


    def test_a_student_can_submit_more_than_once(self):

        self.as_user(self.student)

        first = self.client.post(self.url, {'file_url': upload()}, format='multipart')

        second = self.client.post(self.url, {'file_url': upload('v2.pdf')}, format='multipart')

        self.assertEqual(first.status_code, 201)

        self.assertEqual(second.status_code, 201)

        self.assertEqual(

            Submission.objects.filter(

                assignment=self.assignment, student=self.student

            ).count(),

            2,

        )


    def test_attempts_are_numbered(self):

        self.as_user(self.student)

        self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.client.post(self.url, {'file_url': upload('v2.pdf')}, format='multipart')

        attempts = list(

            Submission.objects.filter(assignment=self.assignment, student=self.student)

            .order_by('attempt')

            .values_list('attempt', flat=True)

        )

        self.assertEqual(attempts, [1, 2])


    def test_only_the_newest_attempt_is_latest(self):

        self.as_user(self.student)

        self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.client.post(self.url, {'file_url': upload('v2.pdf')}, format='multipart')

        latest = Submission.objects.filter(

            assignment=self.assignment, student=self.student, is_latest=True

        )

        self.assertEqual(latest.count(), 1)

        self.assertEqual(latest.first().attempt, 2)


    def test_a_submission_before_the_due_date_is_not_late(self):

        self.as_user(self.student)

        self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.assertFalse(Submission.objects.get(assignment=self.assignment).is_late)


    def test_a_submission_after_the_due_date_is_late(self):

        self.assignment.due_date = timezone.now() - timedelta(days=1)

        self.assignment.save()

        self.as_user(self.student)

        self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.assertTrue(Submission.objects.get(assignment=self.assignment).is_late)


    def test_lateness_is_not_rewritten_when_the_due_date_moves(self):


        self.assignment.due_date = timezone.now() - timedelta(days=1)

        self.assignment.save()

        self.as_user(self.student)

        self.client.post(self.url, {'file_url': upload()}, format='multipart')


        self.assignment.due_date = timezone.now() + timedelta(days=30)

        self.assignment.save()


        self.assertTrue(Submission.objects.get(assignment=self.assignment).is_late)


    def test_an_assignment_with_no_due_date_is_never_late(self):

        self.assignment.due_date = None

        self.assignment.save()

        self.as_user(self.student)

        self.client.post(self.url, {'file_url': upload()}, format='multipart')

        self.assertFalse(Submission.objects.get(assignment=self.assignment).is_late)


class QuizQuestionTypeTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.quiz = Assignment.objects.create(

            course=self.course, title='Mixed quiz', description='x',

            type=Assignment.QUIZ, max_score=100,

        )

        self.url = f'/api/courses/{self.course.id}/assignments/{self.quiz.id}/attempts/'


    def make_question(self, qtype, points, choices=()):

        question = QuizQuestion.objects.create(

            assignment=self.quiz, text='Q', type=qtype, points=points

        )

        made = [

            QuizChoice.objects.create(question=question, text=text, is_correct=correct)

            for text, correct in choices

        ]

        return question, made


    def test_true_false_scores_like_a_single_choice(self):

        question, choices = self.make_question(

            QuizQuestion.TRUE_FALSE, 10, [('True', True), ('False', False)]

        )

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'answers': [{'question': question.id, 'selected_choice': choices[0].id}]},

            format='json',

        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(float(response.data['score']), 10.0)


    def test_multi_select_needs_every_correct_option(self):

        question, choices = self.make_question(

            QuizQuestion.MULTIPLE, 10,

            [('a', True), ('b', True), ('c', False)],

        )

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'answers': [{

                'question': question.id,

                'selected_choices': [choices[0].id, choices[1].id],

            }]},

            format='json',

        )

        self.assertEqual(float(response.data['score']), 10.0)


    def test_multi_select_scores_nothing_for_a_partial_answer(self):

        question, choices = self.make_question(

            QuizQuestion.MULTIPLE, 10, [('a', True), ('b', True), ('c', False)]

        )

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'answers': [{'question': question.id, 'selected_choices': [choices[0].id]}]},

            format='json',

        )

        self.assertEqual(float(response.data['score']), 0.0)


    def test_multi_select_scores_nothing_when_a_wrong_option_is_included(self):

        question, choices = self.make_question(

            QuizQuestion.MULTIPLE, 10, [('a', True), ('b', True), ('c', False)]

        )

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'answers': [{

                'question': question.id,

                'selected_choices': [choices[0].id, choices[1].id, choices[2].id],

            }]},

            format='json',

        )

        self.assertEqual(float(response.data['score']), 0.0)


    def test_a_written_question_leaves_the_attempt_pending(self):

        question, _ = self.make_question(QuizQuestion.WRITTEN, 20)

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'answers': [{'question': question.id, 'text_answer': 'My essay.'}]},

            format='json',

        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(response.data['needs_manual_grading'])


    def test_a_pending_quiz_records_no_grade_yet(self):


        question, _ = self.make_question(QuizQuestion.WRITTEN, 20)

        self.as_user(self.student)

        self.client.post(

            self.url,

            {'answers': [{'question': question.id, 'text_answer': 'My essay.'}]},

            format='json',

        )

        submission = Submission.objects.get(assignment=self.quiz, student=self.student)

        self.assertIsNone(submission.grade)


    def test_marking_the_written_answer_completes_the_grade(self):

        written, _ = self.make_question(QuizQuestion.WRITTEN, 20)

        mcq, choices = self.make_question(

            QuizQuestion.SINGLE, 10, [('right', True), ('wrong', False)]

        )

        self.as_user(self.student)

        self.client.post(

            self.url,

            {'answers': [

                {'question': written.id, 'text_answer': 'Essay'},

                {'question': mcq.id, 'selected_choice': choices[0].id},

            ]},

            format='json',

        )

        answer = QuizAnswer.objects.get(question=written)


        self.as_user(self.instructor)

        response = self.client.post(

            f'/api/courses/{self.course.id}/assignments/{self.quiz.id}'

            f'/written-answers/{answer.id}/grade/',

            {'awarded_points': 15},

            format='json',

        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(response.data['needs_manual_grading'])


        self.assertEqual(float(response.data['score']), 25.0)


        submission = Submission.objects.get(assignment=self.quiz, student=self.student)

        self.assertEqual(float(submission.grade), 25.0)


    def test_written_marks_are_capped_at_the_question_value(self):

        written, _ = self.make_question(QuizQuestion.WRITTEN, 20)

        self.as_user(self.student)

        self.client.post(

            self.url,

            {'answers': [{'question': written.id, 'text_answer': 'Essay'}]},

            format='json',

        )

        answer = QuizAnswer.objects.get(question=written)


        self.as_user(self.instructor)

        response = self.client.post(

            f'/api/courses/{self.course.id}/assignments/{self.quiz.id}'

            f'/written-answers/{answer.id}/grade/',

            {'awarded_points': 999},

            format='json',

        )

        self.assertEqual(response.status_code, 400)


    def test_students_cannot_mark_written_answers(self):

        written, _ = self.make_question(QuizQuestion.WRITTEN, 20)

        self.as_user(self.student)

        self.client.post(

            self.url,

            {'answers': [{'question': written.id, 'text_answer': 'Essay'}]},

            format='json',

        )

        answer = QuizAnswer.objects.get(question=written)

        response = self.client.post(

            f'/api/courses/{self.course.id}/assignments/{self.quiz.id}'

            f'/written-answers/{answer.id}/grade/',

            {'awarded_points': 20},

            format='json',

        )

        self.assertEqual(response.status_code, 403)


    def test_a_choice_answer_is_rejected_for_a_written_question(self):

        written, _ = self.make_question(QuizQuestion.WRITTEN, 20)

        _, choices = self.make_question(

            QuizQuestion.SINGLE, 10, [('a', True), ('b', False)]

        )

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'answers': [{'question': written.id, 'selected_choice': choices[0].id}]},

            format='json',

        )

        self.assertEqual(response.status_code, 400)


    def test_a_single_choice_question_rejects_several_answers(self):

        question, choices = self.make_question(

            QuizQuestion.SINGLE, 10, [('a', True), ('b', False)]

        )

        self.as_user(self.student)

        response = self.client.post(

            self.url,

            {'answers': [{

                'question': question.id,

                'selected_choices': [choices[0].id, choices[1].id],

            }]},

            format='json',

        )

        self.assertEqual(response.status_code, 400)
