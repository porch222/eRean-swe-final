from django.contrib.auth.models import AbstractUser

from django.db import models


class User(AbstractUser):

    ADMIN = 'admin'

    INSTRUCTOR = 'instructor'

    STUDENT = 'student'


    ROLE_CHOICES = [

        (ADMIN, 'Admin'),

        (INSTRUCTOR, 'Instructor'),

        (STUDENT, 'Student'),

    ]

    role = models.CharField(

        max_length=20, choices=ROLE_CHOICES, default=STUDENT, db_index=True

    )


    major = models.ForeignKey(

        'courses.Major',

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name='students',

    )


    class Meta:

        ordering = ['username']


    def __str__(self):

        return f'{self.username} ({self.role})'


    @property

    def is_admin(self):

        return self.role == self.ADMIN


    @property

    def is_instructor(self):

        return self.role == self.INSTRUCTOR


    @property

    def is_student(self):

        return self.role == self.STUDENT


    @property

    def full_name(self):

        return self.get_full_name() or self.username
