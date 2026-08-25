from django.urls import path


from .views import (

    AcceptAnswerView,

    ReplyDetailView,

    ReplyListCreateView,

    ThreadDetailView,

    ThreadListCreateView,

    ThreadModerateView,

)


urlpatterns = [

    path('', ThreadListCreateView.as_view(), name='thread_list_create'),

    path('<int:pk>/', ThreadDetailView.as_view(), name='thread_detail'),

    path('<int:pk>/moderate/', ThreadModerateView.as_view(), name='thread_moderate'),

    path('<int:thread_pk>/replies/', ReplyListCreateView.as_view(), name='reply_list_create'),

    path('<int:thread_pk>/replies/<int:pk>/', ReplyDetailView.as_view(), name='reply_detail'),

    path(

        '<int:thread_pk>/replies/<int:pk>/accept/',

        AcceptAnswerView.as_view(),

        name='reply_accept',

    ),

]
