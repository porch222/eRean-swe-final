from django.db.models import Count

from rest_framework import generics, permissions

from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework.response import Response

from rest_framework.views import APIView


from courses.views import get_course_content_or_404, log_activity

from notifications.models import Notification, notify

from .models import Reply, Thread

from .serializers import (

    ModerateThreadSerializer,

    ReplySerializer,

    ThreadDetailSerializer,

    ThreadSerializer,

)


def is_course_staff(user, course):


    return user.is_admin or (user.is_instructor and course.instructor_id == user.id)


def can_edit(user, obj, course):


    return obj.author_id == user.id or is_course_staff(user, course)


class ThreadListCreateView(generics.ListCreateAPIView):


    permission_classes = [permissions.IsAuthenticated]


    def get_serializer_class(self):

        return ThreadSerializer


    def get_course(self):

        return get_course_content_or_404(self.kwargs['course_pk'], self.request.user)


    def get_queryset(self):

        course = self.get_course()

        queryset = Thread.objects.filter(course=course).select_related('author').annotate(

            reply_count=Count('replies')

        )

        kind = self.request.query_params.get('kind')

        if kind in (Thread.DISCUSSION, Thread.QUESTION):

            queryset = queryset.filter(kind=kind)

        if self.request.query_params.get('unanswered') == 'true':

            queryset = queryset.filter(kind=Thread.QUESTION).exclude(

                replies__is_answer=True

            )


        return queryset.order_by('-is_pinned', '-created_at', 'id')


    def perform_create(self, serializer):

        course = self.get_course()

        thread = serializer.save(author=self.request.user, course=course)

        log_activity(self.request.user, 'thread_created', thread)


class ThreadDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = ThreadDetailSerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_course(self):

        return get_course_content_or_404(self.kwargs['course_pk'], self.request.user)


    def get_queryset(self):

        return Thread.objects.filter(course=self.get_course()).select_related(

            'author'

        ).prefetch_related('replies__author')


    def perform_update(self, serializer):

        thread = self.get_object()

        if not can_edit(self.request.user, thread, thread.course):

            raise PermissionDenied('You can only edit your own posts.')

        serializer.save()


    def perform_destroy(self, instance):

        if not can_edit(self.request.user, instance, instance.course):

            raise PermissionDenied('You can only delete your own posts.')

        log_activity(self.request.user, 'thread_deleted', instance)

        instance.delete()


class ThreadModerateView(generics.UpdateAPIView):


    serializer_class = ModerateThreadSerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        return Thread.objects.filter(course_id=self.kwargs['course_pk'])


    def perform_update(self, serializer):

        thread = self.get_object()

        if not is_course_staff(self.request.user, thread.course):

            raise PermissionDenied('Only the course instructor or an admin can do that.')

        serializer.save()

        log_activity(self.request.user, 'thread_moderated', thread)


class ReplyListCreateView(generics.ListCreateAPIView):

    serializer_class = ReplySerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_thread(self):

        course = get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        return generics.get_object_or_404(

            Thread.objects.select_related('course'), pk=self.kwargs['thread_pk'], course=course

        )


    def get_queryset(self):

        return Reply.objects.filter(thread=self.get_thread()).select_related('author')


    def perform_create(self, serializer):

        thread = self.get_thread()

        if thread.is_locked and not is_course_staff(self.request.user, thread.course):

            raise ValidationError('This thread is locked.')

        reply = serializer.save(author=self.request.user, thread=thread)


        if thread.author_id != self.request.user.id:

            notify(

                thread.author,

                Notification.REPLY,

                f'{self.request.user.get_full_name() or self.request.user.username} '

                f'replied to "{thread.title}"',

                f'/courses/{thread.course_id}/discussions/{thread.id}',

            )

        return reply


class ReplyDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = ReplySerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        get_course_content_or_404(self.kwargs['course_pk'], self.request.user)

        return Reply.objects.filter(

            thread_id=self.kwargs['thread_pk']

        ).select_related('author', 'thread__course')


    def perform_update(self, serializer):

        reply = self.get_object()

        if not can_edit(self.request.user, reply, reply.thread.course):

            raise PermissionDenied('You can only edit your own posts.')

        serializer.save()


    def perform_destroy(self, instance):

        if not can_edit(self.request.user, instance, instance.thread.course):

            raise PermissionDenied('You can only delete your own posts.')

        instance.delete()


class AcceptAnswerView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def post(self, request, course_pk, thread_pk, pk):

        course = get_course_content_or_404(course_pk, request.user)

        thread = generics.get_object_or_404(Thread, pk=thread_pk, course=course)

        reply = generics.get_object_or_404(Reply, pk=pk, thread=thread)


        if thread.kind != Thread.QUESTION:

            raise ValidationError('Only questions can have an accepted answer.')

        if thread.author_id != request.user.id and not is_course_staff(request.user, course):

            raise PermissionDenied('Only the person who asked can accept an answer.')


        thread.replies.filter(is_answer=True).update(is_answer=False)

        reply.is_answer = True

        reply.save(update_fields=['is_answer'])


        if reply.author_id != request.user.id:

            notify(

                reply.author,

                Notification.REPLY,

                f'Your reply was accepted as the answer to "{thread.title}"',

                f'/courses/{course.id}/discussions/{thread.id}',

            )

        return Response(ReplySerializer(reply).data)
