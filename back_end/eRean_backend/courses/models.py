import os

import uuid


from django.conf import settings

from django.db import models


def material_upload_path(instance, filename):


    ext = os.path.splitext(filename)[1].lower()

    return f'materials/{uuid.uuid4()}{ext}'


class Term(models.Model):


    code = models.CharField(max_length=20, unique=True, help_text='e.g. 2026-FA')

    name = models.CharField(max_length=100, help_text='e.g. Fall 2026')

    year = models.PositiveIntegerField()

    starts_on = models.DateField()

    ends_on = models.DateField()


    is_current = models.BooleanField(default=False)


    class Meta:

        ordering = ['-year', '-starts_on']

        constraints = [

            models.UniqueConstraint(

                fields=['is_current'],

                condition=models.Q(is_current=True),

                name='only_one_current_term',

            ),

            models.CheckConstraint(

                check=models.Q(ends_on__gt=models.F('starts_on')),

                name='term_ends_after_it_starts',

            ),

        ]


    def __str__(self):

        return self.name


    @property

    def is_open(self):


        from django.utils import timezone


        today = timezone.now().date()

        return self.starts_on <= today <= self.ends_on


class Major(models.Model):


    code = models.CharField(max_length=20, unique=True)

    name = models.CharField(max_length=120, unique=True)

    description = models.TextField(blank=True)


    class Meta:

        ordering = ['name']


    def __str__(self):

        return f'{self.code} — {self.name}'


class Curriculum(models.Model):


    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='curricula')

    name = models.CharField(max_length=120)

    year = models.PositiveIntegerField(help_text='Intake year this version applies to.')

    is_active = models.BooleanField(default=True, db_index=True)

    credits_to_graduate = models.PositiveIntegerField(

        null=True,

        blank=True,

        help_text=(

            'Total credits needed for the degree, electives included. Leave '

            'blank to require exactly the required courses and nothing more.'

        ),

    )

    courses = models.ManyToManyField(

        'Course', through='CurriculumCourse', related_name='curricula'

    )


    class Meta:

        ordering = ['major__name', '-year']

        constraints = [

            models.UniqueConstraint(fields=['major', 'year'], name='unique_major_curriculum_year'),

        ]


    def __str__(self):

        return f'{self.name} ({self.year})'


    @property

    def total_credits(self):


        return sum(

            entry.course.credits

            for entry in self.entries.select_related('course')

            if entry.is_required

        )


    @property

    def graduation_credits(self):


        if self.credits_to_graduate is not None:

            return self.credits_to_graduate

        return self.total_credits


class CurriculumCourse(models.Model):


    curriculum = models.ForeignKey(

        Curriculum, on_delete=models.CASCADE, related_name='entries'

    )

    course = models.ForeignKey(

        'Course', on_delete=models.CASCADE, related_name='curriculum_entries'

    )

    year_level = models.PositiveSmallIntegerField(default=1)

    term = models.PositiveSmallIntegerField(default=1)

    is_required = models.BooleanField(default=True)


    class Meta:

        ordering = ['year_level', 'term', 'course__title']

        constraints = [

            models.UniqueConstraint(

                fields=['curriculum', 'course'], name='unique_course_per_curriculum'

            ),

        ]


    def __str__(self):

        return f'{self.course.title} in {self.curriculum.name}'


class Course(models.Model):

    DRAFT = 'draft'

    PUBLISHED = 'published'

    ARCHIVED = 'archived'


    STATUS_CHOICES = [

        (DRAFT, 'Draft'),

        (PUBLISHED, 'Published'),

        (ARCHIVED, 'Archived'),

    ]

    title = models.CharField(max_length=200)

    description = models.TextField()


    major = models.ForeignKey(

        Major, on_delete=models.PROTECT, related_name='courses', null=True, blank=True

    )

    credits = models.PositiveSmallIntegerField(default=3)


    term = models.ForeignKey(

        Term, on_delete=models.PROTECT, related_name='courses', null=True, blank=True

    )

    instructor = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses'

    )

    status = models.CharField(

        max_length=20, choices=STATUS_CHOICES, default=DRAFT, db_index=True

    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    class Meta:

        ordering = ['-created_at', 'id']


    def __str__(self):

        return self.title


class Material(models.Model):

    VIDEO = 'video'

    PDF = 'pdf'

    LINK = 'link'


    TYPE_CHOICES = [

        (VIDEO, 'Video'),

        (PDF, 'PDF'),

        (LINK, 'Link'),

    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')

    title = models.CharField(max_length=200)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)


    file_url = models.FileField(upload_to=material_upload_path, null=True, blank=True)

    link_url = models.URLField(max_length=500, null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)


    class Meta:

        ordering = ['-uploaded_at', 'id']


    def __str__(self):

        return self.title


class Announcement(models.Model):

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')

    author = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements'

    )

    title = models.CharField(max_length=200)

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    edited_at = models.DateTimeField(null=True, blank=True)


    class Meta:

        ordering = ['-created_at', 'id']


    @property

    def is_edited(self):

        return self.edited_at is not None


    def __str__(self):

        return self.title


class AnnouncementRead(models.Model):

    announcement = models.ForeignKey(

        Announcement, on_delete=models.CASCADE, related_name='reads'

    )

    student = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcement_reads'

    )

    read_at = models.DateTimeField(auto_now_add=True)


    class Meta:

        constraints = [

            models.UniqueConstraint(

                fields=['announcement', 'student'], name='unique_announcement_read'

            )

        ]


    def __str__(self):

        return f'{self.student} read {self.announcement_id}'


class ActivityLog(models.Model):

    actor = models.ForeignKey(

        settings.AUTH_USER_MODEL,

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name='activity_logs',

    )

    action = models.CharField(max_length=100, db_index=True)

    target_type = models.CharField(max_length=100, blank=True)

    target_id = models.PositiveIntegerField(null=True, blank=True)

    details = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    class Meta:

        ordering = ['-created_at', 'id']

        indexes = [models.Index(fields=['target_type', 'target_id'])]


    def __str__(self):

        return f'{self.action} at {self.created_at}'
