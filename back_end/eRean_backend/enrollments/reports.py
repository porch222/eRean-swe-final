from rest_framework import generics, permissions

from rest_framework.response import Response

from rest_framework.views import APIView


from eRean_backend.api_helpers import resolve_student_id

from assignments.models import Assignment, Submission

from courses.views import get_owned_course_or_403

from .models import GRADE_POINTS, Enrollment


class GradebookView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request, course_pk):

        course = get_owned_course_or_403(course_pk, request.user)


        assignments = list(Assignment.objects.filter(course=course).order_by('due_date', 'id'))

        enrollments = list(

            course.enrollments.filter(status__in=['active', 'completed'])

            .select_related('student')

            .order_by('student__last_name', 'student__username')

        )


        marks = {}

        submissions = Submission.objects.filter(

            assignment__course=course, is_latest=True

        ).values(

            'student_id', 'assignment_id', 'grade', 'is_late', 'attempt', 'submitted_at'

        )

        for row in submissions:

            marks[(row['student_id'], row['assignment_id'])] = row


        possible = sum(a.max_score for a in assignments)


        students = []

        for enrollment in enrollments:

            cells = []

            earned = 0

            for assignment in assignments:

                row = marks.get((enrollment.student_id, assignment.id))

                grade = row['grade'] if row else None

                if grade is not None:

                    earned += float(grade)

                cells.append({

                    'assignment': assignment.id,

                    'grade': grade,

                    'max_score': assignment.max_score,

                    'submitted': bool(row),

                    'is_late': row['is_late'] if row else False,

                    'attempt': row['attempt'] if row else 0,

                })

            students.append({

                'student': enrollment.student_id,

                'name': enrollment.student.get_full_name() or enrollment.student.username,

                'enrollment': enrollment.id,

                'cells': cells,

                'total': round(earned, 2),

                'percent': round(earned / possible * 100, 2) if possible else None,

                'final_score': enrollment.final_score,

                'letter_grade': enrollment.letter_grade,

                'finalized': enrollment.finalized_at is not None,

            })


        return Response({

            'course': course.id,

            'course_title': course.title,

            'assignments': [

                {

                    'id': a.id, 'title': a.title, 'type': a.type,

                    'max_score': a.max_score, 'due_date': a.due_date,

                }

                for a in assignments

            ],

            'points_possible': possible,

            'students': students,

        })


class TranscriptView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request):

        target_id = resolve_student_id(request)


        enrollments = (

            Enrollment.objects.filter(student_id=target_id)

            .select_related('course', 'course__major', 'course__term')

            .order_by('-course__term__starts_on', '-enrolled_at')

        )


        entries = []

        credits_earned = 0

        credits_attempted = 0

        quality_points = 0.0

        graded_credits = 0


        for enrollment in enrollments:

            if enrollment.status == Enrollment.DROPPED:


                pass

            elif enrollment.finalized_at:

                credits_attempted += enrollment.course.credits

                credits_earned += enrollment.credits_earned

                points = GRADE_POINTS.get(enrollment.letter_grade)

                if points is not None:

                    quality_points += points * enrollment.course.credits

                    graded_credits += enrollment.course.credits


            term = enrollment.course.term

            entries.append({

                'course': enrollment.course_id,

                'course_title': enrollment.course.title,

                'major': enrollment.course.major.name if enrollment.course.major else None,

                'term': term.id if term else None,

                'term_name': term.name if term else None,

                'credits': enrollment.course.credits,

                'status': enrollment.status,

                'final_score': enrollment.final_score,

                'letter_grade': enrollment.letter_grade,

                'credits_earned': enrollment.credits_earned,

                'is_passed': enrollment.is_passed,

                'finalized_at': enrollment.finalized_at,

                'enrolled_at': enrollment.enrolled_at,

            })


        by_term = {}

        for entry in entries:

            key = entry['term_name'] or 'No term'

            bucket = by_term.setdefault(key, {

                'term': entry['term'],

                'term_name': key,

                'entries': [],

                'credits_earned': 0,

            })

            bucket['entries'].append(entry)

            bucket['credits_earned'] += entry['credits_earned']


        return Response({

            'student': target_id,

            'entries': entries,

            'terms': list(by_term.values()),

            'credits_attempted': credits_attempted,

            'credits_earned': credits_earned,


            'gpa': round(quality_points / graded_credits, 2) if graded_credits else None,

        })
