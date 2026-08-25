from django.conf import settings

from django.core.validators import MaxValueValidator, MinValueValidator

from django.db import models


from courses.models import Course


PASS_MARK = 60


GRADE_BANDS = [

    (97, 'A+'), (93, 'A'), (90, 'A-'),

    (87, 'B+'), (83, 'B'), (80, 'B-'),

    (77, 'C+'), (73, 'C'), (70, 'C-'),

    (67, 'D+'), (63, 'D'), (60, 'D-'),

    (0, 'F'),

]


GRADE_POINTS = {

    'A+': 4.0, 'A': 4.0, 'A-': 3.7,

    'B+': 3.3, 'B': 3.0, 'B-': 2.7,

    'C+': 2.3, 'C': 2.0, 'C-': 1.7,

    'D+': 1.3, 'D': 1.0, 'D-': 0.7,

    'F': 0.0,

}


def letter_for(score):


    if score is None:

        return ''

    for threshold, letter in GRADE_BANDS:

        if score >= threshold:

            return letter

    return 'F'


class Enrollment(models.Model):

    ACTIVE = 'active'

    DROPPED = 'dropped'

    COMPLETED = 'completed'


    STATUS_CHOICES = [

        (ACTIVE, 'Active'),

        (DROPPED, 'Dropped'),

        (COMPLETED, 'Completed'),

    ]

    student = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments'

    )

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)

    progress = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        default=0.00,

        validators=[MinValueValidator(0), MaxValueValidator(100)],

    )

    enrolled_at = models.DateTimeField(auto_now_add=True)


    final_score = models.DecimalField(

        max_digits=5, decimal_places=2, null=True, blank=True,

        validators=[MinValueValidator(0), MaxValueValidator(100)],

        help_text='Percentage across all graded work, at the time of finalising.',

    )

    letter_grade = models.CharField(max_length=2, blank=True, default='')

    credits_earned = models.PositiveSmallIntegerField(default=0)

    finalized_at = models.DateTimeField(null=True, blank=True)


    class Meta:

        ordering = ['-enrolled_at', 'id']

        constraints = [

            models.UniqueConstraint(

                fields=['student', 'course'], name='unique_student_course_enrollment'

            )

        ]


    def __str__(self):

        return f'{self.student} → {self.course}'


    @property

    def is_passed(self):


        if self.final_score is None:

            return None

        return self.final_score >= PASS_MARK


    def compute_score(self):


        from assignments.models import Assignment, Submission


        assignments = Assignment.objects.filter(course=self.course)

        possible = sum(a.max_score for a in assignments)

        if not possible:

            return None


        earned = 0


        graded = Submission.objects.filter(

            assignment__course=self.course,

            student=self.student,

            grade__isnull=False,

            is_latest=True,

        )

        for submission in graded:

            earned += float(submission.grade)

        return round(earned / possible * 100, 2)


    def finalize(self):


        from django.utils import timezone


        score = self.compute_score()

        self.final_score = score

        self.letter_grade = letter_for(score)

        self.credits_earned = (

            self.course.credits if score is not None and score >= PASS_MARK else 0

        )

        self.finalized_at = timezone.now()

        self.status = self.COMPLETED

        self.save(update_fields=[

            'final_score', 'letter_grade', 'credits_earned', 'finalized_at', 'status',

        ])

        return self


class DropRequest(models.Model):


    PENDING = 'pending'

    APPROVED = 'approved'

    REJECTED = 'rejected'


    STATUS_CHOICES = [

        (PENDING, 'Pending'),

        (APPROVED, 'Approved'),

        (REJECTED, 'Rejected'),

    ]


    enrollment = models.ForeignKey(

        Enrollment, on_delete=models.CASCADE, related_name='drop_requests'

    )

    reason = models.TextField(blank=True, default='')

    status = models.CharField(

        max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True

    )

    decided_by = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name='drop_decisions',

    )

    decision_note = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    decided_at = models.DateTimeField(null=True, blank=True)


    class Meta:

        ordering = ['-created_at', 'id']

        constraints = [


            models.UniqueConstraint(

                fields=['enrollment'],

                condition=models.Q(status='pending'),

                name='one_pending_drop_request_per_enrollment',

            )

        ]


    def __str__(self):

        return f'Drop request: {self.enrollment} ({self.status})'
