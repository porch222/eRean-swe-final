from django.urls import path


from .views import (

    ActivityLogListView,

    AnnouncementDetailView,

    AnnouncementListCreateView,

    AnnouncementMarkReadView,

    CourseApprovalView,

    CourseDetailView,

    CourseListCreateView,

    CoursePerformanceView,

    CurriculumCourseDetailView,

    CurriculumCourseListCreateView,

    CurriculumDetailView,

    CurriculumProgressView,

    CurriculumListCreateView,

    CurrentTermView,

    MajorDetailView,

    MajorListCreateView,

    TermDetailView,

    TermListCreateView,

    MaterialDownloadView,

    MaterialDetailView,

    MaterialListCreateView,

)


urlpatterns = [

    path('', CourseListCreateView.as_view(), name='course_list_create'),

    path('activity-logs/', ActivityLogListView.as_view(), name='activity_log_list'),

    path('terms/', TermListCreateView.as_view(), name='term_list_create'),

    path('terms/current/', CurrentTermView.as_view(), name='term_current'),

    path('terms/<int:pk>/', TermDetailView.as_view(), name='term_detail'),

    path('majors/', MajorListCreateView.as_view(), name='major_list_create'),

    path('majors/<int:pk>/', MajorDetailView.as_view(), name='major_detail'),

    path('curricula/', CurriculumListCreateView.as_view(), name='curriculum_list_create'),

    path('curricula/<int:pk>/', CurriculumDetailView.as_view(), name='curriculum_detail'),

    path(

        'curricula/<int:pk>/progress/',

        CurriculumProgressView.as_view(),

        name='curriculum_progress',

    ),

    path(

        'curricula/<int:curriculum_pk>/courses/',

        CurriculumCourseListCreateView.as_view(),

        name='curriculum_course_list_create',

    ),

    path(

        'curricula/<int:curriculum_pk>/courses/<int:pk>/',

        CurriculumCourseDetailView.as_view(),

        name='curriculum_course_detail',

    ),

    path('<int:pk>/', CourseDetailView.as_view(), name='course_detail'),

    path('<int:pk>/approve/', CourseApprovalView.as_view(), name='course_approve'),

    path('<int:pk>/performance/', CoursePerformanceView.as_view(), name='course_performance'),

    path('<int:course_pk>/materials/', MaterialListCreateView.as_view(), name='material_list_create'),

    path('<int:course_pk>/materials/<int:pk>/', MaterialDetailView.as_view(), name='material_detail'),

    path('<int:course_pk>/materials/<int:pk>/download/', MaterialDownloadView.as_view(), name='material_download'),

    path('<int:course_pk>/announcements/', AnnouncementListCreateView.as_view(), name='announcement_list_create'),

    path('<int:course_pk>/announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement_detail'),

    path('<int:course_pk>/announcements/<int:pk>/read/', AnnouncementMarkReadView.as_view(), name='announcement_mark_read'),

]
