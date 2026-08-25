from django.conf import settings

from django.db import models


from courses.models import Course


class AttendanceSession(models.Model):


    course = models.ForeignKey(

        Course, on_delete=models.CASCADE, related_name='attendance_sessions'

    )

    date = models.DateField()

    title = models.CharField(max_length=200, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:

        ordering = ['-date', 'id']

        constraints = [

            models.UniqueConstraint(

                fields=['course', 'date'], name='one_attendance_session_per_day'

            )

        ]


    def __str__(self):

        return f'{self.course.title} — {self.date}'


class AttendanceRecord(models.Model):

    PRESENT = 'present'

    ABSENT = 'absent'

    LATE = 'late'

    EXCUSED = 'excused'


    STATUS_CHOICES = [

        (PRESENT, 'Present'),

        (ABSENT, 'Absent'),

        (LATE, 'Late'),

        (EXCUSED, 'Excused'),

    ]


    session = models.ForeignKey(

        AttendanceSession, on_delete=models.CASCADE, related_name='records'

    )

    student = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records'

    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PRESENT)

    note = models.CharField(max_length=200, blank=True, default='')


    class Meta:

        ordering = ['student__username', 'id']

        constraints = [

            models.UniqueConstraint(

                fields=['session', 'student'], name='one_attendance_record_per_student'

            )

        ]


    def __str__(self):

        return f'{self.student} — {self.session.date}: {self.status}'


    @property

    def counts_as_attended(self):


        return self.status in (self.PRESENT, self.LATE)
