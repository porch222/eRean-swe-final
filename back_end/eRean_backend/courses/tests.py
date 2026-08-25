from django.utils import timezone

from django.core.files.uploadedfile import SimpleUploadedFile

from django.urls import reverse

from rest_framework import status


from eRean_backend.testutils import BaseAPITestCase

from enrollments.models import Enrollment

from .models import (

    ActivityLog,

    Announcement,

    AnnouncementRead,

    Course,

    Curriculum,

    CurriculumCourse,

    Major,

    Material,

    Term,

)


def pdf(name='notes.pdf'):

    return SimpleUploadedFile(name, b'%PDF-1.4 fake', content_type='application/pdf')


class CourseVisibilityTests(BaseAPITestCase):

    def test_student_sees_only_published_courses(self):

        self.as_user(self.student)

        response = self.client.get(reverse('course_list_create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


        titles = [c['title'] for c in response.data['results']]

        self.assertIn('Published Course', titles)

        self.assertIn('Another Instructor Course', titles)

        self.assertNotIn('Draft Course', titles)


    def test_instructor_sees_only_their_own_courses(self):

        self.as_user(self.instructor)

        response = self.client.get(reverse('course_list_create'))

        titles = [c['title'] for c in response.data['results']]

        self.assertIn('Published Course', titles)

        self.assertIn('Draft Course', titles)

        self.assertNotIn('Another Instructor Course', titles)


    def test_admin_sees_everything(self):

        self.as_user(self.admin)

        response = self.client.get(reverse('course_list_create'))

        self.assertEqual(response.data['count'], 3)


    def test_student_gets_404_for_a_draft_course(self):

        self.as_user(self.student)

        response = self.client.get(

            reverse('course_detail', kwargs={'pk': self.draft_course.id})

        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_student_status_filter_cannot_reveal_drafts(self):


        self.as_user(self.student)

        response = self.client.get(reverse('course_list_create'), {'status': 'draft'})

        titles = [c['title'] for c in response.data['results']]

        self.assertNotIn('Draft Course', titles)


class CourseManagementTests(BaseAPITestCase):

    def test_student_cannot_create_a_course(self):

        self.as_user(self.student)

        response = self.client.post(

            reverse('course_list_create'),

            {'title': 'Mine', 'description': 'x', 'major': self.major_cs.id},

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_new_course_is_always_a_draft(self):


        self.as_user(self.instructor)

        response = self.client.post(

            reverse('course_list_create'),

            {

                'title': 'Brand New',

                'description': 'x',

                'major': self.major_cs.id,

                'status': 'published',

            },

        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Course.objects.get(title='Brand New').status, Course.DRAFT)


    def test_instructor_cannot_edit_another_instructors_course(self):

        self.as_user(self.instructor)

        response = self.client.patch(

            reverse('course_detail', kwargs={'pk': self.foreign_course.id}),

            {'title': 'Hijacked'},

        )


        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_owner_can_edit_their_course(self):

        self.as_user(self.instructor)

        response = self.client.patch(

            reverse('course_detail', kwargs={'pk': self.course.id}),

            {'title': 'Renamed'},

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.course.refresh_from_db()

        self.assertEqual(self.course.title, 'Renamed')


class CourseApprovalTests(BaseAPITestCase):

    def test_admin_publishes_a_draft(self):

        self.as_user(self.admin)

        response = self.client.patch(

            reverse('course_approve', kwargs={'pk': self.draft_course.id}),

            {'status': 'published'},

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.draft_course.refresh_from_db()

        self.assertEqual(self.draft_course.status, Course.PUBLISHED)


    def test_instructor_cannot_approve_their_own_course(self):

        self.as_user(self.instructor)

        response = self.client.patch(

            reverse('course_approve', kwargs={'pk': self.draft_course.id}),

            {'status': 'published'},

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_approval_cannot_set_status_back_to_draft(self):

        self.as_user(self.admin)

        response = self.client.patch(

            reverse('course_approve', kwargs={'pk': self.course.id}),

            {'status': 'draft'},

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_approval_is_written_to_the_activity_log(self):

        self.as_user(self.admin)

        self.client.patch(

            reverse('course_approve', kwargs={'pk': self.draft_course.id}),

            {'status': 'published'},

        )

        self.assertTrue(

            ActivityLog.objects.filter(action='course_approved', actor=self.admin).exists()

        )


class CoursePerformanceTests(BaseAPITestCase):


    def test_unenrolled_student_cannot_read_performance(self):

        self.as_user(self.other_student)

        response = self.client.get(

            reverse('course_performance', kwargs={'pk': self.course.id})

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_student_cannot_read_performance_of_a_draft_course(self):

        self.as_user(self.student)

        response = self.client.get(

            reverse('course_performance', kwargs={'pk': self.draft_course.id})

        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_enrolled_student_can_read_performance(self):

        self.as_user(self.student)

        response = self.client.get(

            reverse('course_performance', kwargs={'pk': self.course.id})

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['students_enrolled'], 1)


    def test_instructor_cannot_read_another_instructors_performance(self):

        self.as_user(self.instructor)

        response = self.client.get(

            reverse('course_performance', kwargs={'pk': self.foreign_course.id})

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MaterialTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.url = reverse('material_list_create', kwargs={'course_pk': self.course.id})


    def test_link_material_requires_a_url(self):

        self.as_user(self.instructor)

        response = self.client.post(self.url, {'title': 'Docs', 'type': 'link'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_link_material_is_created(self):

        self.as_user(self.instructor)

        response = self.client.post(

            self.url,

            {'title': 'Docs', 'type': 'link', 'link_url': 'https://example.com'},

        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_file_material_is_created_without_exposing_its_path(self):

        self.as_user(self.instructor)

        response = self.client.post(

            self.url, {'title': 'Notes', 'type': 'pdf', 'file_url': pdf()},

            format='multipart',

        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


        self.assertNotIn('file_url', response.data)

        self.assertIsNotNone(response.data['download_url'])


    def test_pdf_type_rejects_a_video_extension(self):

        self.as_user(self.instructor)

        response = self.client.post(

            self.url,

            {'title': 'Wrong', 'type': 'pdf', 'file_url': pdf('movie.mp4')},

            format='multipart',

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_disallowed_extension_is_rejected(self):

        self.as_user(self.instructor)

        response = self.client.post(

            self.url,

            {

                'title': 'Script',

                'type': 'pdf',

                'file_url': SimpleUploadedFile('run.exe', b'MZ', content_type='application/exe'),

            },

            format='multipart',

        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_student_cannot_upload_material(self):

        self.as_user(self.student)

        response = self.client.post(

            self.url, {'title': 'Sneaky', 'type': 'link', 'link_url': 'https://x.com'}

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unenrolled_student_cannot_list_materials(self):

        self.as_user(self.other_student)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_enrolled_student_can_list_materials(self):

        Material.objects.create(

            course=self.course, title='Notes', type='link', link_url='https://x.com'

        )

        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)


class MaterialDownloadTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.link = Material.objects.create(

            course=self.course, title='Docs', type='link', link_url='https://example.com'

        )

        self.file_material = Material.objects.create(

            course=self.course, title='Notes', type='pdf', file_url=pdf()

        )


    def url_for(self, material):

        return reverse(

            'material_download',

            kwargs={'course_pk': self.course.id, 'pk': material.id},

        )


    def test_link_download_returns_the_url(self):

        self.as_user(self.student)

        response = self.client.get(self.url_for(self.link))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['link_url'], 'https://example.com')


    def test_link_access_is_logged(self):


        self.as_user(self.student)

        self.client.get(self.url_for(self.link))

        self.assertTrue(

            ActivityLog.objects.filter(

                action='material_downloaded', target_id=self.link.id

            ).exists()

        )


    def test_file_download_streams_the_file(self):

        self.as_user(self.student)

        response = self.client.get(self.url_for(self.file_material))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('attachment', response['Content-Disposition'])


    def test_unenrolled_student_cannot_download(self):

        self.as_user(self.other_student)

        response = self.client.get(self.url_for(self.file_material))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AnnouncementTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.url = reverse(

            'announcement_list_create', kwargs={'course_pk': self.course.id}

        )

        self.announcement = Announcement.objects.create(

            course=self.course,

            author=self.instructor,

            title='Welcome',

            content='Read the handbook.',

        )


    def detail_url(self):

        return reverse(

            'announcement_detail',

            kwargs={'course_pk': self.course.id, 'pk': self.announcement.id},

        )


    def test_instructor_can_post(self):

        self.as_user(self.instructor)

        response = self.client.post(self.url, {'title': 'Update', 'content': 'Hello'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_a_fresh_announcement_does_not_claim_to_be_edited(self):

        self.as_user(self.student)

        response = self.client.get(self.url)

        row = next(r for r in response.data['results'] if r['id'] == self.announcement.id)

        self.assertFalse(row['is_edited'])


    def test_editing_the_content_marks_it_edited(self):

        self.as_user(self.instructor)

        response = self.client.patch(

            self.detail_url(), {'content': 'Read chapter two instead.'}

        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(response.data['is_edited'])


    def test_a_revision_resurfaces_as_unread(self):


        AnnouncementRead.objects.create(

            announcement=self.announcement, student=self.student

        )


        self.as_user(self.instructor)

        self.client.patch(self.detail_url(), {'content': 'Different advice.'})


        self.assertFalse(

            AnnouncementRead.objects.filter(announcement=self.announcement).exists()

        )

        self.as_user(self.student)

        row = next(

            r for r in self.client.get(self.url).data['results']

            if r['id'] == self.announcement.id

        )

        self.assertFalse(row['is_read'])


    def test_a_revision_notifies_enrolled_students(self):

        from notifications.models import Notification


        self.as_user(self.instructor)

        self.client.patch(self.detail_url(), {'title': 'Welcome (revised)'})


        message = Notification.objects.filter(recipient=self.student).latest('id').message

        self.assertIn('Updated', message)

        self.assertIn('Welcome (revised)', message)


    def test_saving_without_changing_anything_does_not_disturb_readers(self):


        from notifications.models import Notification


        AnnouncementRead.objects.create(

            announcement=self.announcement, student=self.student

        )

        before = Notification.objects.count()


        self.as_user(self.instructor)

        self.client.patch(self.detail_url(), {'title': self.announcement.title})


        self.assertTrue(

            AnnouncementRead.objects.filter(announcement=self.announcement).exists()

        )

        self.assertEqual(Notification.objects.count(), before)


    def test_an_instructor_cannot_edit_another_instructors_announcement(self):

        other = Announcement.objects.create(

            course=self.course, author=self.admin, title='Notice', content='x'

        )

        url = reverse(

            'announcement_detail',

            kwargs={'course_pk': self.course.id, 'pk': other.id},

        )

        self.as_user(self.instructor)

        response = self.client.patch(url, {'title': 'Hijacked'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        other.refresh_from_db()

        self.assertEqual(other.title, 'Notice')


    def test_student_cannot_post(self):

        self.as_user(self.student)

        response = self.client.post(self.url, {'title': 'Hi', 'content': 'Hello'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_unenrolled_student_cannot_read(self):

        self.as_user(self.other_student)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)


    def test_marking_read_is_idempotent(self):

        url = reverse(

            'announcement_mark_read',

            kwargs={'course_pk': self.course.id, 'pk': self.announcement.id},

        )

        self.as_user(self.student)


        first = self.client.post(url)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)


        second = self.client.post(url)

        self.assertEqual(second.status_code, status.HTTP_200_OK)


        self.assertEqual(

            AnnouncementRead.objects.filter(

                announcement=self.announcement, student=self.student

            ).count(),

            1,

        )


    def test_is_read_reflects_the_requesting_user(self):

        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertFalse(response.data['results'][0]['is_read'])


        self.client.post(

            reverse(

                'announcement_mark_read',

                kwargs={'course_pk': self.course.id, 'pk': self.announcement.id},

            )

        )

        response = self.client.get(self.url)

        self.assertTrue(response.data['results'][0]['is_read'])


    def test_instructor_cannot_delete_another_authors_announcement(self):

        other = Announcement.objects.create(

            course=self.course, author=self.admin, title='Admin note', content='x'

        )

        self.as_user(self.instructor)

        response = self.client.delete(

            reverse(

                'announcement_detail',

                kwargs={'course_pk': self.course.id, 'pk': other.id},

            )

        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ActivityLogTests(BaseAPITestCase):

    def test_activity_log_is_admin_only(self):

        url = reverse('activity_log_list')


        self.as_user(self.admin)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)


        self.as_user(self.instructor)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)


        self.as_user(self.student)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)


    def test_course_creation_is_logged(self):

        self.as_user(self.instructor)

        self.client.post(

            reverse('course_list_create'),

            {'title': 'Logged', 'description': 'x', 'major': self.major_cs.id},

        )

        self.assertTrue(

            ActivityLog.objects.filter(action='course_created', actor=self.instructor).exists()

        )


class EnrollmentGatingTests(BaseAPITestCase):

    def test_dropping_removes_content_access(self):

        url = reverse('material_list_create', kwargs={'course_pk': self.course.id})


        self.as_user(self.student)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)


        self.enrollment.status = Enrollment.DROPPED

        self.enrollment.save()


        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)


class MajorAPITests(BaseAPITestCase):


    def test_any_authenticated_user_can_list_majors(self):

        self.as_user(self.student)

        response = self.client.get('/api/courses/majors/')

        self.assertEqual(response.status_code, 200)

        codes = [row['code'] for row in response.data]

        self.assertIn('CS', codes)


    def test_listing_majors_requires_authentication(self):

        response = self.client.get('/api/courses/majors/')

        self.assertEqual(response.status_code, 401)


    def test_admin_can_create_a_major(self):

        self.as_user(self.admin)

        response = self.client.post(

            '/api/courses/majors/', {'code': 'BIO', 'name': 'Biology'}

        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(Major.objects.filter(code='BIO').exists())


    def test_instructor_cannot_create_a_major(self):

        self.as_user(self.instructor)

        response = self.client.post(

            '/api/courses/majors/', {'code': 'BIO', 'name': 'Biology'}

        )

        self.assertEqual(response.status_code, 403)


    def test_student_cannot_create_a_major(self):

        self.as_user(self.student)

        response = self.client.post(

            '/api/courses/majors/', {'code': 'BIO', 'name': 'Biology'}

        )

        self.assertEqual(response.status_code, 403)


    def test_major_codes_are_unique(self):

        self.as_user(self.admin)

        response = self.client.post(

            '/api/courses/majors/', {'code': 'CS', 'name': 'Duplicate'}

        )

        self.assertEqual(response.status_code, 400)


    def test_a_major_with_courses_cannot_be_deleted(self):


        self.as_user(self.admin)

        response = self.client.delete(f'/api/courses/majors/{self.major_cs.id}/')

        self.assertEqual(response.status_code, 400)

        self.assertTrue(Major.objects.filter(pk=self.major_cs.pk).exists())


    def test_an_empty_major_can_be_deleted(self):

        self.as_user(self.admin)

        empty = Major.objects.create(code='EMPTY', name='Empty Major')

        response = self.client.delete(f'/api/courses/majors/{empty.id}/')

        self.assertEqual(response.status_code, 204)

        self.assertFalse(Major.objects.filter(pk=empty.pk).exists())


class CurriculumAPITests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        self.curriculum = Curriculum.objects.create(

            major=self.major_cs, name='BSCS 2026', year=2026

        )


    def test_student_can_read_a_curriculum(self):

        self.as_user(self.student)

        response = self.client.get(f'/api/courses/curricula/{self.curriculum.id}/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['name'], 'BSCS 2026')


    def test_only_admin_can_create_a_curriculum(self):

        self.as_user(self.instructor)

        payload = {'major': self.major_cs.id, 'name': 'Rogue', 'year': 2027}

        self.assertEqual(

            self.client.post('/api/courses/curricula/', payload).status_code, 403

        )

        self.as_user(self.admin)

        self.assertEqual(

            self.client.post('/api/courses/curricula/', payload).status_code, 201

        )


    def test_one_curriculum_per_major_per_year(self):

        self.as_user(self.admin)

        response = self.client.post(

            '/api/courses/curricula/',

            {'major': self.major_cs.id, 'name': 'Clash', 'year': 2026},

        )

        self.assertEqual(response.status_code, 400)


    def test_admin_can_place_a_course_in_a_curriculum(self):

        self.as_user(self.admin)

        response = self.client.post(

            f'/api/courses/curricula/{self.curriculum.id}/courses/',

            {'course': self.course.id, 'year_level': 1, 'term': 1, 'is_required': True},

        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(self.curriculum.entries.count(), 1)


    def test_a_course_cannot_be_added_to_the_same_curriculum_twice(self):

        self.as_user(self.admin)

        url = f'/api/courses/curricula/{self.curriculum.id}/courses/'

        self.client.post(url, {'course': self.course.id})

        response = self.client.post(url, {'course': self.course.id})

        self.assertEqual(response.status_code, 400)


    def test_one_course_can_sit_in_two_curricula(self):


        other = Curriculum.objects.create(

            major=self.major_math, name='BS Math 2026', year=2026

        )

        CurriculumCourse.objects.create(

            curriculum=self.curriculum, course=self.course, year_level=2, is_required=False

        )

        CurriculumCourse.objects.create(

            curriculum=other, course=self.course, year_level=1, is_required=True

        )

        self.assertEqual(self.course.curricula.count(), 2)


    def test_total_credits_counts_required_courses_only(self):

        elective = Course.objects.create(

            title='Elective', description='x', major=self.major_cs,

            instructor=self.instructor, status=Course.PUBLISHED, credits=2,

        )

        CurriculumCourse.objects.create(

            curriculum=self.curriculum, course=self.course, is_required=True

        )

        CurriculumCourse.objects.create(

            curriculum=self.curriculum, course=elective, is_required=False

        )

        self.assertEqual(self.curriculum.total_credits, self.course.credits)


    def test_student_cannot_add_a_course_to_a_curriculum(self):

        self.as_user(self.student)

        response = self.client.post(

            f'/api/courses/curricula/{self.curriculum.id}/courses/',

            {'course': self.course.id},

        )

        self.assertEqual(response.status_code, 403)


class CourseMajorFilterTests(BaseAPITestCase):

    def test_courses_can_be_filtered_by_major_code(self):

        self.as_user(self.student)

        response = self.client.get('/api/courses/?major=MATH')

        self.assertEqual(response.status_code, 200)

        titles = [row['title'] for row in response.data['results']]

        self.assertIn(self.foreign_course.title, titles)

        self.assertNotIn(self.course.title, titles)


    def test_courses_can_be_filtered_by_major_id(self):

        self.as_user(self.student)

        response = self.client.get(f'/api/courses/?major={self.major_cs.id}')

        titles = [row['title'] for row in response.data['results']]

        self.assertIn(self.course.title, titles)

        self.assertNotIn(self.foreign_course.title, titles)


    def test_course_response_includes_major_and_credits(self):

        self.as_user(self.student)

        response = self.client.get(f'/api/courses/{self.course.id}/')

        self.assertEqual(response.data['major_detail']['code'], 'CS')

        self.assertEqual(response.data['credits'], self.course.credits)


    def test_filtering_by_curriculum_returns_only_its_courses(self):

        curriculum = Curriculum.objects.create(

            major=self.major_cs, name='BSCS 2026', year=2026

        )

        CurriculumCourse.objects.create(curriculum=curriculum, course=self.course)

        self.as_user(self.student)

        response = self.client.get(f'/api/courses/?curriculum={curriculum.id}')

        titles = [row['title'] for row in response.data['results']]

        self.assertEqual(titles, [self.course.title])


class CurriculumProgressTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        from assignments.models import Assignment, Submission

        from enrollments.models import Enrollment


        self.curriculum = Curriculum.objects.create(

            major=self.major_cs, name='BSCS 2026', year=2026

        )


        CurriculumCourse.objects.create(

            curriculum=self.curriculum, course=self.course, is_required=True

        )

        CurriculumCourse.objects.create(

            curriculum=self.curriculum, course=self.foreign_course, is_required=False

        )

        self.url = f'/api/courses/curricula/{self.curriculum.id}/progress/'


        assignment = Assignment.objects.create(

            course=self.course, title='Essay', description='x', max_score=100

        )

        Submission.objects.create(assignment=assignment, student=self.student, grade=90)


    def test_credits_are_only_earned_once_the_course_is_finalised(self):

        self.as_user(self.student)

        before = self.client.get(self.url)

        self.assertEqual(before.data['credits_earned_required'], 0)


        self.enrollment.finalize()


        after = self.client.get(self.url)

        self.assertEqual(after.data['credits_earned_required'], self.course.credits)

        self.assertTrue(after.data['is_complete'])


    def test_electives_are_counted_separately(self):

        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertEqual(response.data['credits_required'], self.course.credits)

        self.assertEqual(

            response.data['credits_elective_available'], self.foreign_course.credits

        )


    def test_a_failed_course_earns_nothing(self):

        from assignments.models import Submission

        Submission.objects.filter(student=self.student).update(grade=10)

        self.enrollment.finalize()


        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertEqual(response.data['credits_earned_required'], 0)

        self.assertFalse(response.data['is_complete'])


    def test_an_active_course_counts_as_in_progress(self):

        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertEqual(response.data['credits_in_progress'], self.course.credits)


    def test_a_course_never_taken_is_reported_as_such(self):

        self.as_user(self.student)

        response = self.client.get(self.url)

        entry = next(

            e for e in response.data['entries'] if e['course'] == self.foreign_course.id

        )

        self.assertEqual(entry['status'], 'not_taken')


    def test_a_student_cannot_read_another_students_progress(self):

        self.as_user(self.student)

        response = self.client.get(f'{self.url}?student={self.other_student.id}')

        self.assertEqual(response.status_code, 403)


    def test_staff_can_read_a_students_progress(self):

        self.as_user(self.admin)

        response = self.client.get(f'{self.url}?student={self.student.id}')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['student'], self.student.id)


    def test_the_graduation_bar_defaults_to_the_required_courses(self):

        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertEqual(response.data['credits_to_graduate'], self.course.credits)


    def test_an_admin_can_raise_the_graduation_bar(self):

        self.as_user(self.admin)

        target = self.course.credits + self.foreign_course.credits

        response = self.client.patch(

            f'/api/courses/curricula/{self.curriculum.id}/',

            {'credits_to_graduate': target},

        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['credits_to_graduate'], target)

        self.assertEqual(response.data['graduation_credits'], target)


    def test_a_student_cannot_change_the_graduation_bar(self):

        self.as_user(self.student)

        response = self.client.patch(

            f'/api/courses/curricula/{self.curriculum.id}/',

            {'credits_to_graduate': 1},

        )

        self.assertEqual(response.status_code, 403)

        self.curriculum.refresh_from_db()

        self.assertIsNone(self.curriculum.credits_to_graduate)


    def test_the_bar_cannot_be_set_below_the_required_courses(self):


        self.as_user(self.admin)

        response = self.client.patch(

            f'/api/courses/curricula/{self.curriculum.id}/',

            {'credits_to_graduate': self.course.credits - 1},

        )

        self.assertEqual(response.status_code, 400)

        self.curriculum.refresh_from_db()

        self.assertIsNone(self.curriculum.credits_to_graduate)


    def test_required_courses_alone_do_not_graduate_you_under_a_raised_bar(self):


        self.curriculum.credits_to_graduate = (

            self.course.credits + self.foreign_course.credits

        )

        self.curriculum.save()

        self.enrollment.finalize()


        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertEqual(

            response.data['credits_earned_required'], self.course.credits

        )

        self.assertFalse(response.data['is_complete'])


    def test_electives_cannot_substitute_for_a_required_course(self):


        from enrollments.models import Enrollment


        self.curriculum.credits_to_graduate = self.course.credits

        self.curriculum.save()


        elective = Enrollment.objects.create(

            student=self.student, course=self.foreign_course

        )

        elective.status = Enrollment.COMPLETED

        elective.final_score = 95

        elective.letter_grade = 'A'

        elective.credits_earned = self.foreign_course.credits

        elective.finalized_at = timezone.now()

        elective.save()


        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertGreaterEqual(

            response.data['credits_earned_total'], self.course.credits

        )

        self.assertFalse(response.data['is_complete'])


    def test_percent_never_exceeds_one_hundred(self):

        from enrollments.models import Enrollment


        elective = Enrollment.objects.create(

            student=self.student, course=self.foreign_course

        )

        elective.status = Enrollment.COMPLETED

        elective.final_score = 95

        elective.finalized_at = timezone.now()

        elective.save()

        self.enrollment.finalize()


        self.as_user(self.student)

        response = self.client.get(self.url)

        self.assertLessEqual(response.data['percent_complete'], 100)


    def test_an_empty_curriculum_does_not_divide_by_zero(self):

        empty = Curriculum.objects.create(

            major=self.major_math, name='Empty', year=2027

        )

        self.as_user(self.student)

        response = self.client.get(f'/api/courses/curricula/{empty.id}/progress/')

        self.assertEqual(response.status_code, 200)

        self.assertIsNone(response.data['percent_complete'])

        self.assertFalse(response.data['is_complete'])


class TermTests(BaseAPITestCase):

    def setUp(self):

        super().setUp()

        from datetime import date

        self.term = Term.objects.create(

            code='2026-FA', name='Fall 2026', year=2026,

            starts_on=date(2026, 8, 24), ends_on=date(2026, 12, 18), is_current=True,

        )

        self.old = Term.objects.create(

            code='2025-FA', name='Fall 2025', year=2025,

            starts_on=date(2025, 8, 25), ends_on=date(2025, 12, 19),

        )


    def test_anyone_signed_in_can_list_terms(self):

        self.as_user(self.student)

        response = self.client.get('/api/courses/terms/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual({t['code'] for t in response.data}, {'2026-FA', '2025-FA'})


    def test_only_admin_can_create_a_term(self):

        from datetime import date

        payload = {

            'code': '2027-SP', 'name': 'Spring 2027', 'year': 2027,

            'starts_on': '2027-01-11', 'ends_on': '2027-05-14',

        }

        self.as_user(self.instructor)

        self.assertEqual(self.client.post('/api/courses/terms/', payload).status_code, 403)

        self.as_user(self.admin)

        self.assertEqual(self.client.post('/api/courses/terms/', payload).status_code, 201)


    def test_a_term_must_end_after_it_starts(self):

        self.as_user(self.admin)

        response = self.client.post('/api/courses/terms/', {

            'code': '2027-BAD', 'name': 'Backwards', 'year': 2027,

            'starts_on': '2027-05-14', 'ends_on': '2027-01-11',

        })

        self.assertEqual(response.status_code, 400)


    def test_term_codes_are_unique(self):

        self.as_user(self.admin)

        response = self.client.post('/api/courses/terms/', {

            'code': '2026-FA', 'name': 'Clash', 'year': 2026,

            'starts_on': '2026-08-24', 'ends_on': '2026-12-18',

        })

        self.assertEqual(response.status_code, 400)


    def test_promoting_a_term_demotes_the_previous_current_one(self):


        self.as_user(self.admin)

        response = self.client.patch(

            f'/api/courses/terms/{self.old.id}/', {'is_current': True}

        )

        self.assertEqual(response.status_code, 200)

        self.term.refresh_from_db()

        self.old.refresh_from_db()

        self.assertTrue(self.old.is_current)

        self.assertFalse(self.term.is_current)

        self.assertEqual(Term.objects.filter(is_current=True).count(), 1)


    def test_current_term_endpoint(self):

        self.as_user(self.student)

        response = self.client.get('/api/courses/terms/current/')

        self.assertEqual(response.data['code'], '2026-FA')


    def test_current_term_is_null_when_none_is_set(self):

        Term.objects.update(is_current=False)

        self.as_user(self.student)

        response = self.client.get('/api/courses/terms/current/')

        self.assertIsNone(response.data)


    def test_a_term_with_courses_cannot_be_deleted(self):

        self.course.term = self.term

        self.course.save()

        self.as_user(self.admin)

        response = self.client.delete(f'/api/courses/terms/{self.term.id}/')

        self.assertEqual(response.status_code, 400)

        self.assertTrue(Term.objects.filter(pk=self.term.pk).exists())


    def test_an_empty_term_can_be_deleted(self):

        self.as_user(self.admin)

        response = self.client.delete(f'/api/courses/terms/{self.old.id}/')

        self.assertEqual(response.status_code, 204)


    def test_courses_filter_by_term_code(self):

        self.course.term = self.term

        self.course.save()

        self.foreign_course.term = self.old

        self.foreign_course.save()


        self.as_user(self.student)

        response = self.client.get('/api/courses/?term=2026-FA')

        titles = [c['title'] for c in response.data['results']]

        self.assertIn(self.course.title, titles)

        self.assertNotIn(self.foreign_course.title, titles)


    def test_courses_filter_by_current_term(self):

        self.course.term = self.term

        self.course.save()

        self.foreign_course.term = self.old

        self.foreign_course.save()


        self.as_user(self.student)

        response = self.client.get('/api/courses/?term=current')

        titles = [c['title'] for c in response.data['results']]

        self.assertEqual(titles, [self.course.title])


    def test_the_same_course_can_run_in_two_terms(self):


        Course.objects.create(

            title=self.course.title, description=self.course.description,

            major=self.course.major, instructor=self.instructor,

            status=Course.PUBLISHED, term=self.old,

        )

        self.course.term = self.term

        self.course.save()

        self.assertEqual(Course.objects.filter(title=self.course.title).count(), 2)


    def test_course_response_carries_its_term(self):

        self.course.term = self.term

        self.course.save()

        self.as_user(self.student)

        response = self.client.get(f'/api/courses/{self.course.id}/')

        self.assertEqual(response.data['term_detail']['code'], '2026-FA')


class CompletedEnrollmentAccessTests(BaseAPITestCase):


    def test_a_completed_student_can_still_read_course_content(self):

        self.enrollment.status = Enrollment.COMPLETED

        self.enrollment.save()

        self.as_user(self.student)

        url = reverse('material_list_create', kwargs={'course_pk': self.course.id})

        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)


    def test_a_dropped_student_still_cannot(self):

        self.enrollment.status = Enrollment.DROPPED

        self.enrollment.save()

        self.as_user(self.student)

        url = reverse('material_list_create', kwargs={'course_pk': self.course.id})

        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
