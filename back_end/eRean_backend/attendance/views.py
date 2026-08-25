from django.db.models import Count, Q

from rest_framework import generics, permissions

from rest_framework.exceptions import ValidationError

from rest_framework.response import Response

from rest_framework.views import APIView


from eRean_backend.api_helpers import resolve_student_id

from courses.views import (

    get_course_content_or_404,

    get_owned_course_or_403,

    log_activity,

)

from .models import AttendanceRecord, AttendanceSession

from .serializers import (

    AttendanceRecordSerializer,

    AttendanceSessionSerializer,

    MarkAttendanceSerializer,

)


class SessionListCreateView(generics.ListCreateAPIView):


    serializer_class = AttendanceSessionSerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        course = get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        return AttendanceSession.objects.filter(course=course).prefetch_related(

            'records__student'

        )


    def perform_create(self, serializer):

        course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)


        if AttendanceSession.objects.filter(

            course=course, date=serializer.validated_data['date']

        ).exists():

            raise ValidationError('Attendance for that date has already been started.')

        session = serializer.save(course=course)

        log_activity(self.request.user, 'attendance_session_created', session)


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = AttendanceSessionSerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        if self.request.method in permissions.SAFE_METHODS:

            course = get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        else:

            course = get_owned_course_or_403(self.kwargs['course_pk'], self.request.user)

        return AttendanceSession.objects.filter(course=course).prefetch_related(

            'records__student'

        )


class MarkAttendanceView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, course_pk, pk):

        course = get_owned_course_or_403(course_pk, request.user)

        session = generics.get_object_or_404(AttendanceSession, pk=pk, course=course)


        serializer = MarkAttendanceSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)


        enrolled = set(

            course.enrollments.filter(status='active').values_list('student_id', flat=True)

        )

        for row in serializer.validated_data['records']:

            student_id = row['student']

            if student_id not in enrolled:

                continue

            AttendanceRecord.objects.update_or_create(

                session=session,

                student_id=student_id,

                defaults={

                    'status': row.get('status', AttendanceRecord.PRESENT),

                    'note': row.get('note', ''),

                },

            )


        log_activity(request.user, 'attendance_marked', session)

        session.refresh_from_db()

        return Response(AttendanceSessionSerializer(session).data)


class MyAttendanceView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, course_pk):

        course = get_course_content_or_404(course_pk, request.user)


        target_id = resolve_student_id(request)


        records = AttendanceRecord.objects.filter(

            session__course=course, student_id=target_id

        ).select_related('session')


        held = AttendanceSession.objects.filter(course=course).count()

        attended = sum(1 for r in records if r.counts_as_attended)

        return Response({

            'course': course.id,

            'student': target_id,

            'sessions_held': held,

            'sessions_recorded': records.count(),

            'attended': attended,


            'attendance_rate': round(attended / held * 100, 1) if held else None,

            'records': [

                {

                    'session': r.session_id,

                    'date': r.session.date,

                    'title': r.session.title,

                    'status': r.status,

                    'note': r.note,

                }

                for r in records

            ],

        })


class CourseAttendanceSummaryView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, course_pk):

        course = get_owned_course_or_403(course_pk, request.user)

        held = AttendanceSession.objects.filter(course=course).count()


        rows = (

            course.enrollments.filter(status='active')

            .select_related('student')

            .annotate(

                attended=Count(

                    'student__attendance_records',

                    filter=Q(student__attendance_records__session__course=course)

                    & Q(student__attendance_records__status__in=['present', 'late']),

                    distinct=True,

                )

            )

        )

        return Response({

            'course': course.id,

            'sessions_held': held,

            'students': [

                {

                    'student': e.student_id,

                    'name': e.student.get_full_name() or e.student.username,

                    'attended': e.attended,

                    'attendance_rate': round(e.attended / held * 100, 1) if held else None,

                }

                for e in rows

            ],

        })
