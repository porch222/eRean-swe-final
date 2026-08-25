from django.urls import reverse

from rest_framework import status


from eRean_backend.testutils import PASSWORD, BaseAPITestCase

from .models import User


class RegistrationTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.url = reverse('register')


    def payload(self, **overrides):

        data = {

            'username': 'newstudent',

            'email': 'new@test.local',

            'password': 'strongpassword123',

            'password_confirm': 'strongpassword123',

            'first_name': 'New',

            'last_name': 'Student',

        }

        data.update(overrides)

        return data


    def test_registration_succeeds_and_hashes_the_password(self):

        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


        user = User.objects.get(username='newstudent')

        self.assertTrue(user.check_password('strongpassword123'))

        self.assertNotEqual(user.password, 'strongpassword123')


    def test_registration_always_creates_a_student(self):


        response = self.client.post(self.url, self.payload(role='admin'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(User.objects.get(username='newstudent').role, User.STUDENT)


    def test_password_must_be_confirmed(self):

        response = self.client.post(

            self.url, self.payload(password_confirm='somethingelse')

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('password_confirm', response.data)


    def test_weak_password_is_rejected(self):

        response = self.client.post(

            self.url, self.payload(password='123', password_confirm='123')

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('password', response.data)


    def test_password_matching_the_username_is_rejected(self):

        response = self.client.post(

            self.url,

            self.payload(

                username='alexander', password='alexander1', password_confirm='alexander1'

            ),

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_duplicate_username_gives_a_generic_message(self):


        response = self.client.post(self.url, self.payload(username='student1'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        body = str(response.data).lower()

        self.assertIn('unable to register', body)

        self.assertNotIn('already exists', body)


    def test_duplicate_email_is_rejected(self):

        response = self.client.post(self.url, self.payload(email='student1@test.local'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthTests(BaseAPITestCase):

    def test_login_returns_tokens_and_the_user(self):

        response = self.client.post(

            reverse('token_obtain_pair'),

            {'username': 'student1', 'password': PASSWORD},

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('access', response.data)

        self.assertIn('refresh', response.data)

        self.assertEqual(response.data['user']['username'], 'student1')

        self.assertEqual(response.data['user']['role'], 'student')


    def test_login_with_a_bad_password_fails(self):

        response = self.client.post(

            reverse('token_obtain_pair'),

            {'username': 'student1', 'password': 'wrong'},

        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_refresh_token_issues_a_new_access_token(self):

        login = self.client.post(

            reverse('token_obtain_pair'),

            {'username': 'student1', 'password': PASSWORD},

        )

        response = self.client.post(

            reverse('token_refresh'), {'refresh': login.data['refresh']}

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('access', response.data)


    def test_logout_blacklists_the_refresh_token(self):

        login = self.client.post(

            reverse('token_obtain_pair'),

            {'username': 'student1', 'password': PASSWORD},

        )

        refresh = login.data['refresh']


        self.as_user(self.student)

        logout = self.client.post(reverse('logout'), {'refresh': refresh})

        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)


        self.client.force_authenticate(user=None)

        reuse = self.client.post(reverse('token_refresh'), {'refresh': refresh})

        self.assertEqual(reuse.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(BaseAPITestCase):

    def test_me_requires_authentication(self):

        response = self.client.get(reverse('me'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_me_returns_the_current_user_without_the_password(self):

        self.as_user(self.student)

        response = self.client.get(reverse('me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['username'], 'student1')

        self.assertNotIn('password', response.data)


    def test_user_can_edit_their_own_profile(self):

        self.as_user(self.student)

        response = self.client.patch(reverse('me'), {'first_name': 'Updated'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.student.refresh_from_db()

        self.assertEqual(self.student.first_name, 'Updated')


    def test_user_cannot_promote_themselves(self):


        self.as_user(self.student)

        response = self.client.patch(reverse('me'), {'role': 'admin'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.student.refresh_from_db()

        self.assertEqual(self.student.role, User.STUDENT)


    def test_password_change_requires_the_current_password(self):

        self.as_user(self.student)

        response = self.client.post(

            reverse('password_change'),

            {

                'current_password': 'wrong',

                'new_password': 'BrandNewPass!99',

                'new_password_confirm': 'BrandNewPass!99',

            },

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_password_change_succeeds(self):

        self.as_user(self.student)

        response = self.client.post(

            reverse('password_change'),

            {

                'current_password': PASSWORD,

                'new_password': 'BrandNewPass!99',

                'new_password_confirm': 'BrandNewPass!99',

            },

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.student.refresh_from_db()

        self.assertTrue(self.student.check_password('BrandNewPass!99'))


class AdminUserManagementTests(BaseAPITestCase):

    def test_user_list_is_admin_only(self):

        url = reverse('user_list')


        self.as_user(self.admin)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)


        self.as_user(self.instructor)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)


        self.as_user(self.student)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)


    def test_student_cannot_read_another_users_detail(self):

        url = reverse('user_detail', kwargs={'pk': self.admin.id})

        self.as_user(self.student)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)


    def test_admin_can_promote_a_student_to_instructor(self):

        self.as_user(self.admin)

        response = self.client.patch(

            reverse('user_detail', kwargs={'pk': self.student.id}),

            {'role': 'instructor'},

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.student.refresh_from_db()

        self.assertEqual(self.student.role, User.INSTRUCTOR)


    def test_admin_can_create_an_instructor_account(self):

        self.as_user(self.admin)

        response = self.client.post(

            reverse('user_list'),

            {

                'username': 'newteacher',

                'email': 'newteacher@test.local',

                'password': 'strongpassword123',

                'role': 'instructor',

            },

        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(User.objects.get(username='newteacher').role, User.INSTRUCTOR)


    def test_admin_cannot_delete_their_own_account(self):

        self.as_user(self.admin)

        response = self.client.delete(

            reverse('user_detail', kwargs={'pk': self.admin.id})

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())


    def test_the_last_admin_cannot_be_demoted(self):

        self.as_user(self.admin)

        response = self.client.patch(

            reverse('user_detail', kwargs={'pk': self.admin.id}), {'role': 'student'}

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MajorAssignmentPermissionTests(BaseAPITestCase):


    def setUp(self):

        super().setUp()

        self.student.major = self.major_cs

        self.student.save(update_fields=['major'])


    def test_student_cannot_change_their_own_major(self):

        self.as_user(self.student)

        response = self.client.patch('/api/users/me/', {'major': self.major_math.id})

        self.student.refresh_from_db()


        self.assertEqual(self.student.major, self.major_cs)

        self.assertEqual(response.status_code, 200)


    def test_admin_can_assign_a_students_major(self):

        self.as_user(self.admin)

        response = self.client.patch(

            f'/api/users/{self.student.id}/', {'major': self.major_math.id}

        )

        self.assertEqual(response.status_code, 200)

        self.student.refresh_from_db()

        self.assertEqual(self.student.major, self.major_math)


    def test_instructor_cannot_assign_a_students_major(self):

        self.as_user(self.instructor)

        response = self.client.patch(

            f'/api/users/{self.student.id}/', {'major': self.major_math.id}

        )

        self.assertIn(response.status_code, (403, 404))

        self.student.refresh_from_db()

        self.assertEqual(self.student.major, self.major_cs)
