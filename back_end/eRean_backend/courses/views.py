from django.db.models import Avg, Count, Q

from django.http import FileResponse

from django.utils import timezone

from rest_framework import generics, permissions, status

from django.shortcuts import get_object_or_404

from eRean_backend.api_helpers import resolve_student_id

from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework.response import Response

from rest_framework.views import APIView


from notifications.models import Notification, notify_many

from users.permissions import IsAdmin, IsAdminOrInstructor

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

from .serializers import (

    ActivityLogSerializer,

    AnnouncementReadSerializer,

    AnnouncementSerializer,

    CourseApprovalSerializer,

    CourseDetailSerializer,

    CoursePerformanceSerializer,

    CourseSerializer,

    CurriculumCourseSerializer,

    CurriculumSerializer,

    MajorSerializer,

    MaterialSerializer,

    TermSerializer,

)


def get_owned_course_or_403(pk, user):


    course = generics.get_object_or_404(Course.objects.all(), pk=pk)

    if user.is_instructor and course.instructor != user:

        raise PermissionDenied('You do not manage this course.')

    if user.is_student:

        raise PermissionDenied('You do not manage this course.')

    return course


def visible_courses_for(user):


    if user.is_admin:

        return Course.objects.all()

    if user.is_instructor:

        return Course.objects.filter(instructor=user)

    return Course.objects.filter(status=Course.PUBLISHED)


def get_visible_course_or_404(pk, user):

    return generics.get_object_or_404(visible_courses_for(user), pk=pk)


def get_course_content_or_404(pk, user):


    course = get_visible_course_or_404(pk, user)

    if user.is_student:


        is_enrolled = course.enrollments.filter(

            student=user, status__in=['active', 'completed']

        ).exists()

        if not is_enrolled:

            raise PermissionDenied('Enroll in this course to view its content.')

    return course


def annotate_courses(queryset):

    return queryset.select_related('instructor').annotate(

        material_count=Count('materials', distinct=True),

        assignment_count=Count('assignments', distinct=True),

        enrolled_count=Count(

            'enrollments', filter=Q(enrollments__status='active'), distinct=True

        ),

    )


def log_activity(actor, action, target=None, details=''):

    ActivityLog.objects.create(

        actor=actor if actor.is_authenticated else None,

        action=action,

        target_type=target.__class__.__name__ if target else '',

        target_id=getattr(target, 'id', None),

        details=details,

    )


class CourseListCreateView(generics.ListCreateAPIView):

    serializer_class = CourseSerializer

    search_fields = [

        'title', 'description', 'major__name', 'major__code',

        'term__name', 'term__code',

    ]

    ordering_fields = ['created_at', 'title', 'credits']

    ordering = ['-created_at']


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdminOrInstructor()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):

        user = self.request.user

        queryset = visible_courses_for(user)


        major = self.request.query_params.get('major')

        if major:

            queryset = (

                queryset.filter(major_id=major)

                if major.isdigit()

                else queryset.filter(major__code__iexact=major)

            )


        term = self.request.query_params.get('term')

        if term == 'current':

            queryset = queryset.filter(term__is_current=True)

        elif term:

            queryset = (

                queryset.filter(term_id=term)

                if term.isdigit()

                else queryset.filter(term__code__iexact=term)

            )


        curriculum = self.request.query_params.get('curriculum')

        if curriculum and str(curriculum).isdigit():

            queryset = queryset.filter(curricula__id=curriculum)


        status_param = self.request.query_params.get('status')

        if status_param and (user.is_admin or user.is_instructor):

            queryset = queryset.filter(status=status_param)


        return annotate_courses(queryset)


    def perform_create(self, serializer):


        course = serializer.save(instructor=self.request.user, status=Course.DRAFT)

        log_activity(self.request.user, 'course_created', course)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = CourseDetailSerializer


    def get_permissions(self):

        if self.request.method == 'GET':

            return [permissions.IsAuthenticated()]

        return [IsAdminOrInstructor()]


    def get_queryset(self):

        return annotate_courses(

            visible_courses_for(self.request.user)

        ).prefetch_related('materials')


    def perform_update(self, serializer):

        course = self.get_object()

        user = self.request.user

        if user.is_instructor and course.instructor != user:

            raise PermissionDenied('You do not manage this course.')

        course = serializer.save()

        log_activity(user, 'course_updated', course)


    def perform_destroy(self, instance):

        user = self.request.user

        if user.is_instructor and instance.instructor != user:

            raise PermissionDenied('You do not manage this course.')

        log_activity(user, 'course_deleted', instance)

        instance.delete()


class CourseApprovalView(APIView):


    permission_classes = [IsAdmin]


    def patch(self, request, pk):

        course = generics.get_object_or_404(Course.objects.all(), pk=pk)

        serializer = CourseApprovalSerializer(course, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        serializer.save()

        log_activity(request.user, 'course_approved', course, f'status={course.status}')


        course = annotate_courses(Course.objects.filter(pk=pk)).first()

        return Response(CourseDetailSerializer(course, context={'request': request}).data)


class CoursePerformanceView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, pk):

        user = request.user

        if user.is_student:

            course = get_course_content_or_404(pk, user)

        else:

            course = get_owned_course_or_403(pk, user)


        enrollments = course.enrollments.all()

        from assignments.models import Submission


        submissions = Submission.objects.filter(assignment__course=course)

        grade_stats = submissions.aggregate(

            total=Count('id'),

            graded=Count('id', filter=Q(grade__isnull=False)),

            avg_grade=Avg('grade'),

        )


        data = {

            'course': course.id,

            'students_enrolled': enrollments.filter(status='active').count(),

            'assignments': course.assignments.count(),

            'submissions': grade_stats['total'],

            'graded_submissions': grade_stats['graded'],

            'average_progress': enrollments.aggregate(avg=Avg('progress'))['avg'] or 0,

            'average_grade': grade_stats['avg_grade'],

        }

        return Response(CoursePerformanceSerializer(data).data)


class MaterialListCreateView(generics.ListCreateAPIView):

    serializer_class = MaterialSerializer


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdminOrInstructor()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):

        course = get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        return Material.objects.filter(course=course)


    def perform_create(self, serializer):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        material = serializer.save(course=course)

        log_activity(self.request.user, 'material_created', material)


class MaterialDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = MaterialSerializer


    def get_permissions(self):

        if self.request.method == 'GET':

            return [permissions.IsAuthenticated()]

        return [IsAdminOrInstructor()]


    def get_queryset(self):

        user = self.request.user

        if user.is_student:

            course = get_course_content_or_404(self.kwargs['course_pk'], user)

        else:

            course = get_visible_course_or_404(self.kwargs['course_pk'], user)

        return Material.objects.filter(course=course)


    def perform_update(self, serializer):

        get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        material = serializer.save()

        log_activity(self.request.user, 'material_updated', material)


    def perform_destroy(self, instance):

        get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        log_activity(self.request.user, 'material_deleted', instance)

        instance.delete()


class MaterialDownloadView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, course_pk, pk):

        course = get_course_content_or_404(course_pk, request.user)

        material = generics.get_object_or_404(Material.objects.all(), pk=pk, course=course)


        if material.type == Material.LINK:

            log_activity(request.user, 'material_downloaded', material, 'type=link')

            return Response({'link_url': material.link_url})

        if not material.file_url:

            return Response(

                {'detail': 'No file is attached to this material.'},

                status=status.HTTP_404_NOT_FOUND,

            )

        log_activity(request.user, 'material_downloaded', material, 'type=file')

        return FileResponse(material.file_url.open('rb'), as_attachment=True)


class AnnouncementListCreateView(generics.ListCreateAPIView):

    serializer_class = AnnouncementSerializer

    search_fields = ['title', 'content']

    ordering_fields = ['created_at']

    ordering = ['-created_at']


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdminOrInstructor()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):

        course = get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        return Announcement.objects.filter(course=course).select_related('author')


    def perform_create(self, serializer):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        announcement = serializer.save(course=course, author=self.request.user)

        log_activity(self.request.user, 'announcement_created', announcement)

        notify_many(

            [

                e.student for e in announcement.course.enrollments

                .filter(status='active').select_related('student')

            ],

            Notification.ANNOUNCEMENT,

            f'{announcement.course.title}: {announcement.title}',

            f'/courses/{announcement.course_id}',

        )


class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = AnnouncementSerializer


    def get_permissions(self):

        if self.request.method == 'GET':

            return [permissions.IsAuthenticated()]

        return [IsAdminOrInstructor()]


    def get_queryset(self):

        course = get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        return Announcement.objects.filter(course=course).select_related('author')


    def perform_update(self, serializer):

        announcement = self.get_object()

        user = self.request.user


        if user.is_instructor and announcement.author != user:

            raise PermissionDenied('You can only edit your own announcements.')


        before = Announcement.objects.filter(pk=announcement.pk).values(

            'title', 'content'

        ).first()


        announcement = serializer.save()

        log_activity(user, 'announcement_updated', announcement)


        changed = before and (

            before['title'] != announcement.title

            or before['content'] != announcement.content

        )

        if changed:

            announcement.edited_at = timezone.now()

            announcement.save(update_fields=['edited_at'])


            announcement.reads.all().delete()

            notify_many(

                [

                    e.student for e in announcement.course.enrollments

                    .filter(status='active').select_related('student')

                ],

                Notification.ANNOUNCEMENT,

                f'Updated — {announcement.course.title}: {announcement.title}',

                f'/courses/{announcement.course_id}',

            )


    def perform_destroy(self, instance):

        user = self.request.user

        if user.is_instructor and instance.author != user:

            raise PermissionDenied('You can only delete your own announcements.')

        log_activity(user, 'announcement_deleted', instance)

        instance.delete()


class AnnouncementMarkReadView(APIView):

    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, course_pk, pk):

        course = get_course_content_or_404(course_pk, request.user)

        announcement = generics.get_object_or_404(

            Announcement.objects.all(), pk=pk, course=course

        )

        read, created = AnnouncementRead.objects.get_or_create(

            announcement=announcement, student=request.user

        )

        return Response(

            AnnouncementReadSerializer(read).data,

            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,

        )


class ActivityLogListView(generics.ListAPIView):


    serializer_class = ActivityLogSerializer

    permission_classes = [IsAdmin]

    search_fields = ['action', 'target_type', 'details', 'actor__username']

    ordering_fields = ['created_at', 'action']

    ordering = ['-created_at']


    def get_queryset(self):

        queryset = ActivityLog.objects.select_related('actor')

        action = self.request.query_params.get('action')

        if action:

            queryset = queryset.filter(action=action)

        return queryset


class MajorListCreateView(generics.ListCreateAPIView):


    serializer_class = MajorSerializer

    queryset = Major.objects.annotate(course_count=Count('courses'))

    search_fields = ['code', 'name']

    ordering_fields = ['name', 'code']

    pagination_class = None


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdmin()]

        return [permissions.IsAuthenticated()]


    def perform_create(self, serializer):

        major = serializer.save()

        log_activity(self.request.user, 'major_created', major)


class MajorDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = MajorSerializer

    queryset = Major.objects.annotate(course_count=Count('courses'))


    def get_permissions(self):

        if self.request.method in permissions.SAFE_METHODS:

            return [permissions.IsAuthenticated()]

        return [IsAdmin()]


    def perform_update(self, serializer):

        major = serializer.save()

        log_activity(self.request.user, 'major_updated', major)


    def perform_destroy(self, instance):


        if instance.courses.exists():

            raise ValidationError(

                'This major still has courses. Move or delete them first.'

            )

        log_activity(self.request.user, 'major_deleted', instance)

        instance.delete()


class CurriculumListCreateView(generics.ListCreateAPIView):

    serializer_class = CurriculumSerializer

    search_fields = ['name', 'major__name', 'major__code']

    ordering_fields = ['year', 'name']


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdmin()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):

        queryset = Curriculum.objects.select_related('major').prefetch_related(

            'entries__course'

        )

        major = self.request.query_params.get('major')

        if major:

            queryset = (

                queryset.filter(major_id=major)

                if major.isdigit()

                else queryset.filter(major__code__iexact=major)

            )

        if self.request.query_params.get('active') == 'true':

            queryset = queryset.filter(is_active=True)

        return queryset


    def perform_create(self, serializer):

        curriculum = serializer.save()

        log_activity(self.request.user, 'curriculum_created', curriculum)


class CurriculumDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = CurriculumSerializer

    queryset = Curriculum.objects.select_related('major').prefetch_related('entries__course')


    def get_permissions(self):

        if self.request.method in permissions.SAFE_METHODS:

            return [permissions.IsAuthenticated()]

        return [IsAdmin()]


    def perform_update(self, serializer):

        curriculum = serializer.save()

        log_activity(self.request.user, 'curriculum_updated', curriculum)


    def perform_destroy(self, instance):

        log_activity(self.request.user, 'curriculum_deleted', instance)

        instance.delete()


class CurriculumCourseListCreateView(generics.ListCreateAPIView):


    serializer_class = CurriculumCourseSerializer

    pagination_class = None


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdmin()]

        return [permissions.IsAuthenticated()]


    def get_curriculum(self):

        return get_object_or_404(Curriculum, pk=self.kwargs['curriculum_pk'])


    def get_queryset(self):

        return CurriculumCourse.objects.filter(

            curriculum=self.get_curriculum()

        ).select_related('course')


    def get_serializer_context(self):

        return {**super().get_serializer_context(), 'curriculum': self.get_curriculum()}


    def perform_create(self, serializer):

        entry = serializer.save(curriculum=self.get_curriculum())

        log_activity(self.request.user, 'curriculum_course_added', entry.curriculum)


class CurriculumCourseDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = CurriculumCourseSerializer


    def get_permissions(self):

        if self.request.method in permissions.SAFE_METHODS:

            return [permissions.IsAuthenticated()]

        return [IsAdmin()]


    def get_queryset(self):

        return CurriculumCourse.objects.filter(

            curriculum_id=self.kwargs['curriculum_pk']

        ).select_related('course', 'curriculum')


    def perform_destroy(self, instance):

        log_activity(self.request.user, 'curriculum_course_removed', instance.curriculum)

        instance.delete()


class CurriculumProgressView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, pk):

        from enrollments.models import Enrollment


        curriculum = get_object_or_404(

            Curriculum.objects.select_related('major').prefetch_related('entries__course'),

            pk=pk,

        )


        target_id = resolve_student_id(request)


        enrollments = {

            e.course_id: e

            for e in Enrollment.objects.filter(student_id=target_id).select_related('course')

        }


        entries = []

        required_total = earned_required = 0

        elective_total = earned_elective = 0

        in_progress = 0


        for entry in curriculum.entries.all():

            enrollment = enrollments.get(entry.course_id)

            credits = entry.course.credits

            passed = bool(enrollment and enrollment.finalized_at and enrollment.is_passed)

            active = bool(

                enrollment and enrollment.status == Enrollment.ACTIVE

            )


            if entry.is_required:

                required_total += credits

                if passed:

                    earned_required += credits

            else:

                elective_total += credits

                if passed:

                    earned_elective += credits


            if active:

                in_progress += credits


            entries.append({

                'course': entry.course_id,

                'course_title': entry.course.title,

                'credits': credits,

                'year_level': entry.year_level,

                'term': entry.term,

                'is_required': entry.is_required,

                'status': enrollment.status if enrollment else 'not_taken',

                'letter_grade': enrollment.letter_grade if enrollment else '',

                'final_score': enrollment.final_score if enrollment else None,

                'passed': passed,

            })


        target = curriculum.graduation_credits

        earned_total = earned_required + earned_elective


        is_complete = (

            target > 0

            and earned_required >= required_total

            and earned_total >= target

        )


        return Response({

            'curriculum': curriculum.id,

            'curriculum_name': curriculum.name,

            'major': curriculum.major.name,

            'student': target_id,

            'credits_required': required_total,

            'credits_earned_required': earned_required,

            'credits_elective_available': elective_total,

            'credits_earned_elective': earned_elective,

            'credits_to_graduate': target,

            'credits_earned_total': earned_total,

            'credits_in_progress': in_progress,


            'percent_complete': (

                round(min(earned_total / target * 100, 100), 1) if target else None

            ),

            'is_complete': is_complete,

            'entries': entries,

        })


class TermListCreateView(generics.ListCreateAPIView):


    serializer_class = TermSerializer

    queryset = Term.objects.annotate(course_count=Count('courses'))

    search_fields = ['code', 'name']

    ordering_fields = ['year', 'starts_on', 'code']

    pagination_class = None


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdmin()]

        return [permissions.IsAuthenticated()]


    def perform_create(self, serializer):


        term = serializer.save()

        log_activity(self.request.user, 'term_created', term)


class TermDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = TermSerializer

    queryset = Term.objects.annotate(course_count=Count('courses'))


    def get_permissions(self):

        if self.request.method in permissions.SAFE_METHODS:

            return [permissions.IsAuthenticated()]

        return [IsAdmin()]


    def perform_update(self, serializer):

        term = serializer.save()

        log_activity(self.request.user, 'term_updated', term)


    def perform_destroy(self, instance):


        if instance.courses.exists():

            raise ValidationError(

                'This term still has courses. Move or delete them first.'

            )

        log_activity(self.request.user, 'term_deleted', instance)

        instance.delete()


class CurrentTermView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request):


        term = Term.objects.annotate(course_count=Count('courses')).filter(

            is_current=True

        ).first()

        return Response(TermSerializer(term).data if term else None)
