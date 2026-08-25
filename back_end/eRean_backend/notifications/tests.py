from eRean_backend.testutils import BaseAPITestCase

from .models import Notification, notify, notify_many


class NotificationTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.mine = notify(self.student, Notification.GRADE, 'Your essay was graded')

        self.theirs = notify(self.other_student, Notification.GRADE, 'Not for you')


    def test_a_user_only_sees_their_own(self):

        self.as_user(self.student)

        response = self.client.get('/api/notifications/')

        messages = [row['message'] for row in response.data['results']]

        self.assertIn('Your essay was graded', messages)

        self.assertNotIn('Not for you', messages)


    def test_another_users_notification_is_not_reachable_by_id(self):

        self.as_user(self.student)

        response = self.client.get(f'/api/notifications/{self.theirs.id}/')

        self.assertEqual(response.status_code, 404)


    def test_cannot_mark_someone_elses_as_read(self):

        self.as_user(self.student)

        response = self.client.patch(

            f'/api/notifications/{self.theirs.id}/', {'is_read': True}

        )

        self.assertEqual(response.status_code, 404)

        self.theirs.refresh_from_db()

        self.assertFalse(self.theirs.is_read)


    def test_unread_count(self):

        self.as_user(self.student)

        response = self.client.get('/api/notifications/unread-count/')

        self.assertEqual(response.data['unread'], 1)


    def test_marking_one_as_read(self):

        self.as_user(self.student)

        self.client.patch(f'/api/notifications/{self.mine.id}/', {'is_read': True})

        self.mine.refresh_from_db()

        self.assertTrue(self.mine.is_read)


    def test_mark_all_read_only_touches_your_own(self):

        notify(self.student, Notification.ANNOUNCEMENT, 'Another')

        self.as_user(self.student)

        response = self.client.post('/api/notifications/read-all/')

        self.assertEqual(response.data['marked_read'], 2)

        self.theirs.refresh_from_db()

        self.assertFalse(self.theirs.is_read)


    def test_unread_filter(self):

        self.mine.is_read = True

        self.mine.save()

        notify(self.student, Notification.ANNOUNCEMENT, 'Fresh')

        self.as_user(self.student)

        response = self.client.get('/api/notifications/?unread=true')

        self.assertEqual(len(response.data['results']), 1)


    def test_notify_many_writes_one_row_each(self):

        notify_many([self.student, self.other_student], Notification.ANNOUNCEMENT, 'All')

        self.assertEqual(Notification.objects.filter(message='All').count(), 2)


    def test_notify_with_no_recipient_is_a_no_op(self):

        self.assertIsNone(notify(None, Notification.GRADE, 'nobody'))


    def test_anonymous_users_get_nothing(self):

        response = self.client.get('/api/notifications/')

        self.assertEqual(response.status_code, 401)


class NotificationTriggerTests(BaseAPITestCase):


    def test_posting_an_announcement_notifies_enrolled_students(self):

        self.as_user(self.instructor)

        self.client.post(

            f'/api/courses/{self.course.id}/announcements/',

            {'title': 'Class cancelled', 'content': 'See you next week'},

        )

        self.assertTrue(

            Notification.objects.filter(

                recipient=self.student, kind=Notification.ANNOUNCEMENT

            ).exists()

        )


    def test_new_coursework_notifies_enrolled_students(self):

        self.as_user(self.instructor)

        self.client.post(

            f'/api/courses/{self.course.id}/assignments/',

            {'title': 'Essay 2', 'description': 'x', 'max_score': 50},

        )

        self.assertTrue(

            Notification.objects.filter(

                recipient=self.student, kind=Notification.ASSIGNMENT

            ).exists()

        )


    def test_a_student_not_enrolled_is_not_notified(self):

        self.as_user(self.instructor)

        self.client.post(

            f'/api/courses/{self.course.id}/announcements/',

            {'title': 'Internal', 'content': 'x'},

        )

        self.assertFalse(

            Notification.objects.filter(recipient=self.other_student).exists()

        )
