from django.urls import path


from .views import (

    CourseAttendanceSummaryView,

    MarkAttendanceView,

    MyAttendanceView,

    SessionDetailView,

    SessionListCreateView,

)


urlpatterns = [

    path('', SessionListCreateView.as_view(), name='attendance_session_list'),

    path('me/', MyAttendanceView.as_view(), name='attendance_mine'),

    path('summary/', CourseAttendanceSummaryView.as_view(), name='attendance_summary'),

    path('<int:pk>/', SessionDetailView.as_view(), name='attendance_session_detail'),

    path('<int:pk>/mark/', MarkAttendanceView.as_view(), name='attendance_mark'),

]
