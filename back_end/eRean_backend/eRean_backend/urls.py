from django.contrib import admin

from django.urls import include, path


from assignments.views import MySubmissionsView

from enrollments.reports import GradebookView

from eRean_backend.views import health


urlpatterns = [


    path('health', health, name='health'),

    path('django-admin/', admin.site.urls),

    path('api/', include('users.urls')),

    path('api/my-submissions/', MySubmissionsView.as_view(), name='my_submissions'),

    path('api/courses/', include('courses.urls')),

    path('api/enrollments/', include('enrollments.urls')),

    path('api/notifications/', include('notifications.urls')),

    path('api/courses/<int:course_pk>/discussions/', include('discussions.urls')),

    path('api/courses/<int:course_pk>/attendance/', include('attendance.urls')),

    path('api/courses/<int:course_pk>/gradebook/', GradebookView.as_view(), name='gradebook'),

    path('api/courses/<int:course_pk>/assignments/', include('assignments.urls')),

]
