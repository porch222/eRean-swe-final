from rest_framework import generics, permissions

from rest_framework.response import Response

from rest_framework.views import APIView


from .models import Notification

from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):


    serializer_class = NotificationSerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        queryset = Notification.objects.filter(recipient=self.request.user)

        if self.request.query_params.get('unread') == 'true':

            queryset = queryset.filter(is_read=False)

        return queryset


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):


    serializer_class = NotificationSerializer

    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):

        return Notification.objects.filter(recipient=self.request.user)


class UnreadCountView(APIView):

    permission_classes = [permissions.IsAuthenticated]


    def get(self, request):

        count = Notification.objects.filter(recipient=request.user, is_read=False).count()

        return Response({'unread': count})


class MarkAllReadView(APIView):

    permission_classes = [permissions.IsAuthenticated]


    def post(self, request):

        updated = Notification.objects.filter(

            recipient=request.user, is_read=False

        ).update(is_read=True)

        return Response({'marked_read': updated})
