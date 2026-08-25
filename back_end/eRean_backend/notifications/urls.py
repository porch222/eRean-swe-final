from django.urls import path


from .views import (

    MarkAllReadView,

    NotificationDetailView,

    NotificationListView,

    UnreadCountView,

)


urlpatterns = [

    path('', NotificationListView.as_view(), name='notification_list'),

    path('unread-count/', UnreadCountView.as_view(), name='notification_unread_count'),

    path('read-all/', MarkAllReadView.as_view(), name='notification_read_all'),

    path('<int:pk>/', NotificationDetailView.as_view(), name='notification_detail'),

]
