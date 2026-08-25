from django.utils import timezone

from rest_framework import generics, permissions

from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework.response import Response

from rest_framework.views import APIView


from notifications.models import Notification, notify

from users.permissions import IsStudent

from .models import DropRequest, Enrollment

from .serializers import (

    DropDecisionSerializer,

    DropRequestSerializer,

    EnrollmentSerializer,

    StudentEnrollmentSerializer,

)


def enrollments_for(user):


    queryset = Enrollment.objects.select_related('student', 'course')

    if user.is_admin:

        return queryset

    if user.is_instructor:

        return queryset.filter(course__instructor=user)

    return queryset.filter(student=user)


class EnrollmentListCreateView(generics.ListCreateAPIView):

    serializer_class = EnrollmentSerializer

    search_fields = ['course__title', 'student__username']

    ordering_fields = ['enrolled_at', 'progress', 'status']

    ordering = ['-enrolled_at']


    def get_permissions(self):


        if self.request.method == 'POST':

            return [IsStudent()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):

        queryset = enrollments_for(self.request.user)


        course_id = self.request.query_params.get('course')

        if course_id and course_id.isdigit():

            queryset = queryset.filter(course_id=int(course_id))


        status_param = self.request.query_params.get('status')

        if status_param:

            queryset = queryset.filter(status=status_param)


        return queryset


    def perform_create(self, serializer):

        serializer.save(student=self.request.user)


class EnrollmentDetailView(generics.RetrieveUpdateDestroyAPIView):

    permission_classes = [permissions.IsAuthenticated]


    def get_serializer_class(self):

        if self.request.user.is_student:

            return StudentEnrollmentSerializer

        return EnrollmentSerializer


    def get_queryset(self):

        return enrollments_for(self.request.user)


    def perform_update(self, serializer):

        enrollment = self.get_object()

        if self.request.user.is_student and enrollment.student != self.request.user:

            raise PermissionDenied('This is not your enrollment.')

        serializer.save()


    def perform_destroy(self, instance):


        if self.request.user.is_student:

            raise PermissionDenied(

                'Ask your instructor to drop this course — raise a drop request.'

            )

        instance.delete()


def can_decide(user, course):


    return user.is_admin or (user.is_instructor and course.instructor_id == user.id)


class DropRequestListCreateView(generics.ListCreateAPIView):


    serializer_class = DropRequestSerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        user = self.request.user

        queryset = DropRequest.objects.select_related(

            'enrollment__student', 'enrollment__course', 'decided_by'

        )

        if user.is_admin:

            pass

        elif user.is_instructor:

            queryset = queryset.filter(enrollment__course__instructor=user)

        else:

            queryset = queryset.filter(enrollment__student=user)


        status_param = self.request.query_params.get('status')

        if status_param:

            queryset = queryset.filter(status=status_param)

        return queryset


    def perform_create(self, serializer):

        if not self.request.user.is_student:

            raise PermissionDenied('Only students raise drop requests.')

        drop = serializer.save()

        course = drop.enrollment.course

        notify(

            course.instructor,

            Notification.DROP_REQUEST,

            f'{drop.enrollment.student.get_full_name() or drop.enrollment.student.username} '

            f'asked to drop {course.title}',

            '/enrollments',

        )


class DropRequestDecisionView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, pk):

        drop = generics.get_object_or_404(

            DropRequest.objects.select_related('enrollment__course', 'enrollment__student'),

            pk=pk,

        )

        if not can_decide(request.user, drop.enrollment.course):

            raise PermissionDenied('Only the course instructor or an admin can decide this.')

        if drop.status != DropRequest.PENDING:

            raise ValidationError('That request has already been decided.')


        serializer = DropDecisionSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)


        drop.status = serializer.validated_data['status']

        drop.decision_note = serializer.validated_data.get('decision_note', '')

        drop.decided_by = request.user

        drop.decided_at = timezone.now()

        drop.save(update_fields=['status', 'decision_note', 'decided_by', 'decided_at'])


        if drop.status == DropRequest.APPROVED:

            drop.enrollment.status = Enrollment.DROPPED

            drop.enrollment.save(update_fields=['status'])


        notify(

            drop.enrollment.student,

            Notification.DROP_DECISION,

            f'Your request to drop {drop.enrollment.course.title} was {drop.status}',

            '/enrollments',

        )

        return Response(DropRequestSerializer(drop).data)


class FinalizeGradeView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, pk):

        enrollment = generics.get_object_or_404(

            Enrollment.objects.select_related('course', 'student'), pk=pk

        )

        if not can_decide(request.user, enrollment.course):

            raise PermissionDenied('Only the course instructor or an admin can do that.')


        enrollment.finalize()

        notify(

            enrollment.student,

            Notification.GRADE,

            f'Your final grade for {enrollment.course.title} is '

            f'{enrollment.letter_grade} ({enrollment.final_score}%)',

            '/grades',

        )

        return Response(EnrollmentSerializer(enrollment).data)
