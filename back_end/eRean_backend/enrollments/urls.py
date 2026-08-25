from django.urls import path


from .reports import TranscriptView

from .views import (

    DropRequestDecisionView,

    DropRequestListCreateView,

    EnrollmentDetailView,

    EnrollmentListCreateView,

    FinalizeGradeView,

)


urlpatterns = [

    path('', EnrollmentListCreateView.as_view(), name='enrollment_list_create'),

    path('transcript/', TranscriptView.as_view(), name='transcript'),

    path('drop-requests/', DropRequestListCreateView.as_view(), name='drop_request_list'),

    path(

        'drop-requests/<int:pk>/decide/',

        DropRequestDecisionView.as_view(),

        name='drop_request_decide',

    ),

    path('<int:pk>/', EnrollmentDetailView.as_view(), name='enrollment_detail'),

    path('<int:pk>/finalize/', FinalizeGradeView.as_view(), name='enrollment_finalize'),

]
