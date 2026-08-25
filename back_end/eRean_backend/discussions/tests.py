from eRean_backend.testutils import BaseAPITestCase

from notifications.models import Notification

from .models import Reply, Thread


class DiscussionTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.base = f'/api/courses/{self.course.id}/discussions/'

        self.thread = Thread.objects.create(

            course=self.course, author=self.student, title='Hello', body='World'

        )


    def test_enrolled_student_can_post_a_thread(self):

        self.as_user(self.student)

        response = self.client.post(

            self.base, {'title': 'Q1', 'body': 'How does this work?', 'kind': 'question'}

        )

        self.assertEqual(response.status_code, 201)


    def test_a_student_not_enrolled_cannot_read_the_board(self):


        self.as_user(self.other_student)

        self.assertEqual(self.client.get(self.base).status_code, 403)


    def test_replying_notifies_the_thread_author(self):

        self.as_user(self.instructor)

        self.client.post(f'{self.base}{self.thread.id}/replies/', {'body': 'Here you go'})

        self.assertTrue(

            Notification.objects.filter(

                recipient=self.student, kind=Notification.REPLY

            ).exists()

        )


    def test_replying_to_yourself_does_not_notify_you(self):

        self.as_user(self.student)

        self.client.post(f'{self.base}{self.thread.id}/replies/', {'body': 'Never mind'})

        self.assertFalse(Notification.objects.filter(recipient=self.student).exists())


    def test_author_can_edit_their_own_thread(self):

        self.as_user(self.student)

        response = self.client.patch(

            f'{self.base}{self.thread.id}/', {'title': 'Edited'}

        )

        self.assertEqual(response.status_code, 200)


    def test_another_student_cannot_edit_someone_elses_thread(self):

        other = Thread.objects.create(

            course=self.course, author=self.instructor, title='Staff', body='x'

        )

        self.as_user(self.student)

        response = self.client.patch(f'{self.base}{other.id}/', {'title': 'Hacked'})

        self.assertEqual(response.status_code, 403)


    def test_instructor_can_delete_any_thread(self):

        self.as_user(self.instructor)

        response = self.client.delete(f'{self.base}{self.thread.id}/')

        self.assertEqual(response.status_code, 204)


    def test_only_staff_can_pin_or_lock(self):

        self.as_user(self.student)

        response = self.client.patch(

            f'{self.base}{self.thread.id}/moderate/', {'is_pinned': True}

        )

        self.assertEqual(response.status_code, 403)


        self.as_user(self.instructor)

        response = self.client.patch(

            f'{self.base}{self.thread.id}/moderate/', {'is_pinned': True}

        )

        self.assertEqual(response.status_code, 200)

        self.thread.refresh_from_db()

        self.assertTrue(self.thread.is_pinned)


    def test_pinning_cannot_be_smuggled_through_the_normal_update(self):

        self.as_user(self.student)

        self.client.patch(f'{self.base}{self.thread.id}/', {'is_pinned': True})

        self.thread.refresh_from_db()

        self.assertFalse(self.thread.is_pinned)


    def test_a_locked_thread_refuses_student_replies(self):

        self.thread.is_locked = True

        self.thread.save()

        self.as_user(self.student)

        response = self.client.post(

            f'{self.base}{self.thread.id}/replies/', {'body': 'Anyone?'}

        )

        self.assertEqual(response.status_code, 400)


    def test_staff_can_still_reply_to_a_locked_thread(self):

        self.thread.is_locked = True

        self.thread.save()

        self.as_user(self.instructor)

        response = self.client.post(

            f'{self.base}{self.thread.id}/replies/', {'body': 'Closing note'}

        )

        self.assertEqual(response.status_code, 201)


class QuestionAnswerTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.base = f'/api/courses/{self.course.id}/discussions/'

        self.question = Thread.objects.create(

            course=self.course, author=self.student,

            title='Why?', body='Explain', kind=Thread.QUESTION,

        )

        self.reply = Reply.objects.create(

            thread=self.question, author=self.instructor, body='Because.'

        )


    def accept_url(self, reply):

        return f'{self.base}{self.question.id}/replies/{reply.id}/accept/'


    def test_the_asker_can_accept_an_answer(self):

        self.as_user(self.student)

        response = self.client.post(self.accept_url(self.reply))

        self.assertEqual(response.status_code, 200)

        self.reply.refresh_from_db()

        self.assertTrue(self.reply.is_answer)


    def test_an_unrelated_student_cannot_accept(self):

        Thread.objects.filter(pk=self.question.pk).update(author=self.other_student)

        self.as_user(self.student)

        response = self.client.post(self.accept_url(self.reply))

        self.assertEqual(response.status_code, 403)


    def test_accepting_a_second_reply_moves_the_mark(self):

        second = Reply.objects.create(

            thread=self.question, author=self.instructor, body='Actually...'

        )

        self.as_user(self.student)

        self.client.post(self.accept_url(self.reply))

        self.client.post(self.accept_url(second))


        self.reply.refresh_from_db()

        second.refresh_from_db()

        self.assertFalse(self.reply.is_answer)

        self.assertTrue(second.is_answer)

        self.assertEqual(self.question.replies.filter(is_answer=True).count(), 1)


    def test_a_discussion_cannot_have_an_accepted_answer(self):

        discussion = Thread.objects.create(

            course=self.course, author=self.student, title='Chat', body='x'

        )

        reply = Reply.objects.create(

            thread=discussion, author=self.instructor, body='hi'

        )

        self.as_user(self.student)

        response = self.client.post(

            f'{self.base}{discussion.id}/replies/{reply.id}/accept/'

        )

        self.assertEqual(response.status_code, 400)


    def test_students_cannot_mark_their_own_reply_as_the_answer_directly(self):


        mine = Reply.objects.create(

            thread=self.question, author=self.student, body='I think...'

        )

        self.as_user(self.student)

        self.client.patch(

            f'{self.base}{self.question.id}/replies/{mine.id}/', {'is_answer': True}

        )

        mine.refresh_from_db()

        self.assertFalse(mine.is_answer)


    def test_unanswered_filter(self):

        self.as_user(self.student)

        response = self.client.get(f'{self.base}?unanswered=true')

        titles = [row['title'] for row in response.data['results']]

        self.assertIn('Why?', titles)


        self.reply.is_answer = True

        self.reply.save()

        response = self.client.get(f'{self.base}?unanswered=true')

        titles = [row['title'] for row in response.data['results']]

        self.assertNotIn('Why?', titles)
