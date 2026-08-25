from django.conf import settings

from django.db import models


from courses.models import Course


class Thread(models.Model):


    DISCUSSION = 'discussion'

    QUESTION = 'question'


    KIND_CHOICES = [

        (DISCUSSION, 'Discussion'),

        (QUESTION, 'Question'),

    ]


    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='threads')

    author = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='threads'

    )

    kind = models.CharField(

        max_length=20, choices=KIND_CHOICES, default=DISCUSSION, db_index=True

    )

    title = models.CharField(max_length=200)

    body = models.TextField()

    is_pinned = models.BooleanField(default=False)

    is_locked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    updated_at = models.DateTimeField(auto_now=True)


    class Meta:


        ordering = ['-is_pinned', '-created_at', 'id']


    def __str__(self):

        return self.title


    @property

    def is_answered(self):

        return self.kind == self.QUESTION and self.replies.filter(is_answer=True).exists()


class Reply(models.Model):

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='replies')

    author = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='replies'

    )

    body = models.TextField()


    is_answer = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    updated_at = models.DateTimeField(auto_now=True)


    class Meta:

        ordering = ['created_at', 'id']

        constraints = [


            models.UniqueConstraint(

                fields=['thread'],

                condition=models.Q(is_answer=True),

                name='one_accepted_answer_per_thread',

            )

        ]


    def __str__(self):

        return f'Reply by {self.author} on {self.thread}'
