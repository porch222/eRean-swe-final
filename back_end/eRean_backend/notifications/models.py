from django.conf import settings

from django.db import models


class Notification(models.Model):


    GRADE = 'grade'

    ASSIGNMENT = 'assignment'

    ANNOUNCEMENT = 'announcement'

    REPLY = 'reply'

    DROP_REQUEST = 'drop_request'

    DROP_DECISION = 'drop_decision'

    ATTENDANCE = 'attendance'


    KIND_CHOICES = [

        (GRADE, 'Grade posted'),

        (ASSIGNMENT, 'New coursework'),

        (ANNOUNCEMENT, 'Announcement'),

        (REPLY, 'Discussion reply'),

        (DROP_REQUEST, 'Drop request'),

        (DROP_DECISION, 'Drop decision'),

        (ATTENDANCE, 'Attendance'),

    ]


    recipient = models.ForeignKey(

        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'

    )

    kind = models.CharField(max_length=30, choices=KIND_CHOICES, db_index=True)

    message = models.CharField(max_length=300)


    link_url = models.CharField(max_length=300, blank=True, default='')

    is_read = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    class Meta:

        ordering = ['-created_at', 'id']

        indexes = [models.Index(fields=['recipient', 'is_read'])]


    def __str__(self):

        return f'{self.recipient}: {self.message[:50]}'


def notify(recipient, kind, message, link_url=''):


    if not recipient:

        return None

    return Notification.objects.create(

        recipient=recipient, kind=kind, message=message, link_url=link_url

    )


def notify_many(recipients, kind, message, link_url=''):


    rows = [

        Notification(recipient=user, kind=kind, message=message, link_url=link_url)

        for user in recipients

    ]

    return Notification.objects.bulk_create(rows)
