import os

import uuid


from django.conf import settings

from django.core.validators import MinValueValidator

from django.db import models

from django.utils import timezone


from courses.models import Course


def submission_upload_path(instance, filename):

    ext = os.path.splitext(filename)[1].lower()

    return f'submissions/{uuid.uuid4()}{ext}'


class Assignment(models.Model):

    ASSIGNMENT = 'assignment'

    QUIZ = 'quiz'


    TYPE_CHOICES = [

        (ASSIGNMENT, 'Assignment'),

        (QUIZ, 'Quiz'),

    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')

    title = models.CharField(max_length=200)

    description = models.TextField()

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=ASSIGNMENT)

    due_date = models.DateTimeField(null=True, blank=True)

    max_score = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:

        ordering = ['-created_at', 'id']


    def __str__(self):

        return self.title


class Submission(models.Model):

    assignment = models.ForeignKey(

        Assignment, on_delete=models.CASCADE, related_name='submissions'

    )

    student = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions'

    )

    file_url = models.FileField(upload_to=submission_upload_path, null=True, blank=True)

    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    feedback = models.TextField(blank=True, default='')

    submitted_at = models.DateTimeField(auto_now_add=True)


    attempt = models.PositiveSmallIntegerField(default=1)

    is_latest = models.BooleanField(default=True, db_index=True)


    is_late = models.BooleanField(default=False)


    class Meta:

        ordering = ['-submitted_at', 'id']

        constraints = [

            models.UniqueConstraint(

                fields=['assignment', 'student', 'attempt'],

                name='unique_assignment_submission_attempt',

            )

        ]


    def __str__(self):

        return f'{self.student} - {self.assignment} (attempt {self.attempt})'


    def save(self, *args, **kwargs):

        if self._state.adding:

            previous = Submission.objects.filter(

                assignment=self.assignment, student=self.student

            )

            self.attempt = (previous.aggregate(models.Max('attempt'))['attempt__max'] or 0) + 1

            due = self.assignment.due_date

            self.is_late = bool(due and timezone.now() > due)


            previous.update(is_latest=False)

            self.is_latest = True

        super().save(*args, **kwargs)


    @property

    def is_graded(self):

        return self.grade is not None


class QuizQuestion(models.Model):

    SINGLE = 'single'

    MULTIPLE = 'multiple'

    TRUE_FALSE = 'true_false'

    WRITTEN = 'written'


    TYPE_CHOICES = [

        (SINGLE, 'Multiple choice (one answer)'),

        (MULTIPLE, 'Multiple choice (several answers)'),

        (TRUE_FALSE, 'True or false'),

        (WRITTEN, 'Written answer'),

    ]


    assignment = models.ForeignKey(

        Assignment, on_delete=models.CASCADE, related_name='questions'

    )

    text = models.TextField()

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=SINGLE)

    points = models.PositiveIntegerField(default=1)

    order = models.PositiveIntegerField(default=0)


    @property

    def is_auto_graded(self):


        return self.type != self.WRITTEN


    class Meta:

        ordering = ['order', 'id']


    def __str__(self):

        return self.text[:80]


class QuizChoice(models.Model):

    question = models.ForeignKey(

        QuizQuestion, on_delete=models.CASCADE, related_name='choices'

    )

    text = models.CharField(max_length=500)

    is_correct = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=0)


    class Meta:

        ordering = ['order', 'id']


    def __str__(self):

        return self.text[:80]


class QuizAttempt(models.Model):

    assignment = models.ForeignKey(

        Assignment, on_delete=models.CASCADE, related_name='quiz_attempts'

    )

    student = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts'

    )

    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    submitted_at = models.DateTimeField(auto_now_add=True)


    needs_manual_grading = models.BooleanField(default=False, db_index=True)

    graded_at = models.DateTimeField(null=True, blank=True)


    class Meta:

        ordering = ['-submitted_at', 'id']

        constraints = [

            models.UniqueConstraint(

                fields=['assignment', 'student'], name='unique_quiz_attempt'

            )

        ]


    def __str__(self):

        return f'{self.student} - {self.assignment}'


    def recalculate(self):


        total = 0

        pending = False

        for question in self.assignment.questions.all():

            answers = [a for a in self.answers.all() if a.question_id == question.id]

            if question.type == QuizQuestion.WRITTEN:

                awarded = next(

                    (a.awarded_points for a in answers if a.awarded_points is not None), None

                )

                if awarded is None:

                    pending = True

                else:

                    total += float(awarded)

            elif question.type == QuizQuestion.MULTIPLE:

                correct = {c.id for c in question.choices.all() if c.is_correct}

                chosen = {a.selected_choice_id for a in answers}


                if correct and chosen == correct:

                    total += question.points

            else:

                if answers and answers[0].is_correct:

                    total += question.points


        self.score = round(total, 2)

        self.needs_manual_grading = pending

        self.save(update_fields=['score', 'needs_manual_grading'])

        return self.score


class QuizAnswer(models.Model):

    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')

    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')


    selected_choice = models.ForeignKey(

        QuizChoice, on_delete=models.CASCADE, related_name='answers',

        null=True, blank=True,

    )

    text_answer = models.TextField(blank=True, default='')

    is_correct = models.BooleanField(default=False)


    awarded_points = models.DecimalField(

        max_digits=5, decimal_places=2, null=True, blank=True

    )


    class Meta:

        ordering = ['question__order', 'id']

        constraints = [


            models.UniqueConstraint(

                fields=['attempt', 'question', 'selected_choice'],

                name='unique_answer_per_question_choice',

            )

        ]


    def __str__(self):

        return f'{self.attempt} - {self.question_id}'
