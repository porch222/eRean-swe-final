from django.http import FileResponse

from django.utils import timezone

from rest_framework import generics, permissions, status

from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework.response import Response

from rest_framework.views import APIView


from courses.views import get_course_content_or_404, get_owned_course_or_403

from enrollments.models import Enrollment

from notifications.models import Notification, notify, notify_many

from users.permissions import IsAdminOrInstructor, IsStudent

from .models import (

    Assignment,

    QuizAnswer,

    QuizAttempt,

    QuizChoice,

    QuizQuestion,

    Submission,

)

from .serializers import (

    AssignmentSerializer,

    GradeSubmissionSerializer,

    GradeWrittenAnswerSerializer,

    QuizAnswerSerializer,

    QuizAttemptCreateSerializer,

    QuizAttemptSerializer,

    QuizChoiceSerializer,

    QuizQuestionSerializer,

    StudentQuizQuestionSerializer,

    SubmissionSerializer,

)


def update_enrollment_progress(student, course):


    total = course.assignments.count()

    if total == 0:

        progress = 0

    else:


        graded = Submission.objects.filter(

            assignment__course=course,

            student=student,

            grade__isnull=False,

            is_latest=True,

        ).count()

        progress = round((graded / total) * 100, 2)

    Enrollment.objects.filter(student=student, course=course).update(progress=progress)


def recalculate_course_progress(course):


    for enrollment in course.enrollments.select_related('student'):

        update_enrollment_progress(enrollment.student, course)


def get_quiz_assignment_or_403(course_pk, assignment_pk, user):


    course = get_course_content_or_404(course_pk, user)

    return generics.get_object_or_404(

        Assignment.objects.all(), pk=assignment_pk, course=course, type=Assignment.QUIZ

    )


def submissions_visible_to(user, course_pk, assignment_pk):

    queryset = Submission.objects.filter(

        assignment_id=assignment_pk, assignment__course_id=course_pk

    ).select_related('student', 'assignment', 'assignment__course')

    if user.is_admin:

        return queryset

    if user.is_instructor:

        return queryset.filter(assignment__course__instructor=user)

    return queryset.filter(student=user)


class AssignmentListCreateView(generics.ListCreateAPIView):

    serializer_class = AssignmentSerializer

    search_fields = ['title', 'description']

    ordering_fields = ['created_at', 'due_date', 'title']

    ordering = ['-created_at']


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdminOrInstructor()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):


        course = get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        return Assignment.objects.filter(course=course)


    def perform_create(self, serializer):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        assignment = serializer.save(course=course)


        recalculate_course_progress(course)

        notify_many(

            [e.student for e in course.enrollments.filter(status='active').select_related('student')],

            Notification.ASSIGNMENT,

            f'New {assignment.type} in {course.title}: {assignment.title}',

            f'/courses/{course.id}/assignments/{assignment.id}',

        )


class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = AssignmentSerializer


    def get_permissions(self):

        if self.request.method == 'GET':

            return [permissions.IsAuthenticated()]

        return [IsAdminOrInstructor()]


    def get_queryset(self):

        user = self.request.user

        if user.is_student:

            course = get_course_content_or_404(self.kwargs['course_pk'], user)

        else:

            course = get_owned_course_or_403(self.kwargs['course_pk'], user)

        return Assignment.objects.filter(course=course)


    def perform_update(self, serializer):

        assignment = self.get_object()

        user = self.request.user

        if user.is_instructor and assignment.course.instructor != user:

            raise PermissionDenied('You do not manage this course.')


        serializer.save()


    def perform_destroy(self, instance):

        user = self.request.user

        if user.is_instructor and instance.course.instructor != user:

            raise PermissionDenied('You do not manage this course.')

        course = instance.course

        instance.delete()

        recalculate_course_progress(course)


class QuizQuestionListCreateView(generics.ListCreateAPIView):

    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsAdminOrInstructor()]

        return [permissions.IsAuthenticated()]


    def get_serializer_class(self):


        if self.request.user.is_student:

            return StudentQuizQuestionSerializer

        return QuizQuestionSerializer


    def get_queryset(self):

        assignment = get_quiz_assignment_or_403(

            self.kwargs['course_pk'], self.kwargs['assignment_pk'], self.request.user

        )

        return assignment.questions.prefetch_related('choices')


    def perform_create(self, serializer):

        get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        assignment = generics.get_object_or_404(

            Assignment.objects.all(),

            pk=self.kwargs['assignment_pk'],

            course_id=self.kwargs['course_pk'],

            type=Assignment.QUIZ,

        )

        serializer.save(assignment=assignment)


class QuizQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = QuizQuestionSerializer

    permission_classes = [IsAdminOrInstructor]


    def get_queryset(self):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        return QuizQuestion.objects.filter(

            assignment_id=self.kwargs['assignment_pk'], assignment__course=course

        )


class QuizChoiceListCreateView(generics.ListCreateAPIView):

    serializer_class = QuizChoiceSerializer

    permission_classes = [IsAdminOrInstructor]


    def get_queryset(self):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        return QuizChoice.objects.filter(

            question_id=self.kwargs['question_pk'],

            question__assignment_id=self.kwargs['assignment_pk'],

            question__assignment__course=course,

        )


    def perform_create(self, serializer):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        question = generics.get_object_or_404(

            QuizQuestion.objects.all(),

            pk=self.kwargs['question_pk'],

            assignment_id=self.kwargs['assignment_pk'],

            assignment__course=course,

        )

        serializer.save(question=question)


class QuizChoiceDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = QuizChoiceSerializer

    permission_classes = [IsAdminOrInstructor]


    def get_queryset(self):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        return QuizChoice.objects.filter(

            question_id=self.kwargs['question_pk'],

            question__assignment_id=self.kwargs['assignment_pk'],

            question__assignment__course=course,

        )


    def perform_destroy(self, instance):


        if instance.answers.exists():

            raise ValidationError(

                'A student has already chosen this answer, so it cannot be '

                'removed. Edit its wording instead.'

            )


        if instance.question.choices.count() <= 2:

            raise ValidationError(

                'A question needs at least two choices. Edit this one rather '

                'than deleting it, or delete the whole question.'

            )


        instance.delete()


class QuizAttemptListCreateView(generics.ListCreateAPIView):

    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsStudent()]

        return [permissions.IsAuthenticated()]


    def get_serializer_class(self):

        if self.request.method == 'POST':

            return QuizAttemptCreateSerializer

        return QuizAttemptSerializer


    def get_queryset(self):

        user = self.request.user

        queryset = QuizAttempt.objects.filter(

            assignment_id=self.kwargs['assignment_pk'],

            assignment__course_id=self.kwargs['course_pk'],

        ).select_related('student').prefetch_related('answers')

        if user.is_admin:

            return queryset

        if user.is_instructor:

            return queryset.filter(assignment__course__instructor=user)

        return queryset.filter(student=user)


    def create(self, request, *args, **kwargs):


        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        attempt = serializer.save()

        update_enrollment_progress(attempt.student, attempt.assignment.course)

        return Response(

            QuizAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED

        )


class SubmissionListCreateView(generics.ListCreateAPIView):

    serializer_class = SubmissionSerializer

    ordering_fields = ['submitted_at', 'grade']

    ordering = ['-submitted_at']


    def get_permissions(self):

        if self.request.method == 'POST':

            return [IsStudent()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):

        return submissions_visible_to(

            self.request.user, self.kwargs['course_pk'], self.kwargs['assignment_pk']

        )


    def perform_create(self, serializer):

        serializer.save(

            student=self.request.user, assignment_id=self.kwargs['assignment_pk']

        )


class SubmissionDetailView(generics.RetrieveUpdateAPIView):


    def get_permissions(self):

        if self.request.method in ('PUT', 'PATCH'):

            return [IsAdminOrInstructor()]

        return [permissions.IsAuthenticated()]


    def get_queryset(self):

        return submissions_visible_to(

            self.request.user, self.kwargs['course_pk'], self.kwargs['assignment_pk']

        )


    def get_serializer_class(self):

        if self.request.method in ('PUT', 'PATCH'):

            return GradeSubmissionSerializer

        return SubmissionSerializer


    def perform_update(self, serializer):

        submission = self.get_object()

        user = self.request.user

        if user.is_instructor and submission.assignment.course.instructor != user:

            raise PermissionDenied('You do not manage this course.')

        serializer.save()

        submission.refresh_from_db()

        update_enrollment_progress(submission.student, submission.assignment.course)

        notify(

            submission.student,

            Notification.GRADE,

            f'{submission.assignment.title} was graded: '

            f'{submission.grade}/{submission.assignment.max_score}',

            f'/courses/{submission.assignment.course_id}'

            f'/assignments/{submission.assignment_id}',

        )


    def update(self, request, *args, **kwargs):

        super().update(request, *args, **kwargs)


        instance = self.get_object()

        return Response(SubmissionSerializer(instance, context={'request': request}).data)


class SubmissionDownloadView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, course_pk, assignment_pk, pk):

        submission = generics.get_object_or_404(

            submissions_visible_to(request.user, course_pk, assignment_pk), pk=pk

        )

        if not submission.file_url:

            return Response(

                {'detail': 'No file is attached to this submission.'},

                status=status.HTTP_404_NOT_FOUND,

            )

        return FileResponse(submission.file_url.open('rb'), as_attachment=True)


class MySubmissionsView(generics.ListAPIView):


    serializer_class = SubmissionSerializer

    permission_classes = [IsStudent]

    ordering_fields = ['submitted_at', 'grade']

    ordering = ['-submitted_at']


    def get_queryset(self):

        return Submission.objects.filter(student=self.request.user).select_related(

            'assignment', 'assignment__course', 'student'

        )


class GradeWrittenAnswerView(APIView):


    permission_classes = [IsAdminOrInstructor]


    def post(self, request, course_pk, assignment_pk, pk):

        course = get_owned_course_or_403(course_pk, request.user)

        answer = generics.get_object_or_404(

            QuizAnswer.objects.select_related('question', 'attempt__assignment', 'attempt__student'),

            pk=pk,

            attempt__assignment_id=assignment_pk,

            attempt__assignment__course=course,

        )

        if answer.question.type != QuizQuestion.WRITTEN:

            raise ValidationError('That question is auto-graded.')


        serializer = GradeWrittenAnswerSerializer(

            data=request.data, context={'answer': answer}

        )

        serializer.is_valid(raise_exception=True)


        answer.awarded_points = serializer.validated_data['awarded_points']

        answer.is_correct = answer.awarded_points >= answer.question.points

        answer.save(update_fields=['awarded_points', 'is_correct'])


        attempt = answer.attempt

        attempt.recalculate()


        if not attempt.needs_manual_grading:

            attempt.graded_at = timezone.now()

            attempt.save(update_fields=['graded_at'])

            Submission.objects.filter(

                assignment=attempt.assignment, student=attempt.student

            ).update(grade=attempt.score, feedback='Quiz marked.')

            update_enrollment_progress(attempt.student, course)

            notify(

                attempt.student,

                Notification.GRADE,

                f'{attempt.assignment.title} was marked: '

                f'{attempt.score}/{attempt.assignment.max_score}',

                f'/courses/{course.id}/assignments/{attempt.assignment_id}',

            )


        return Response(QuizAttemptSerializer(attempt).data)


class PendingWrittenAnswersView(generics.ListAPIView):


    serializer_class = QuizAnswerSerializer

    permission_classes = [IsAdminOrInstructor]


    def get_queryset(self):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        return QuizAnswer.objects.filter(

            attempt__assignment_id=self.kwargs['assignment_pk'],

            attempt__assignment__course=course,

            question__type=QuizQuestion.WRITTEN,

            awarded_points__isnull=True,

        ).select_related('question', 'attempt__student')
