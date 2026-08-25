from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView


from .views import (

    LoginView,

    LogoutView,

    MeView,

    PasswordChangeView,

    RegisterView,

    UserDetailView,

    UserListCreateView,

)


urlpatterns = [

    path('auth/token/', LoginView.as_view(), name='token_obtain_pair'),

    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('auth/register/', RegisterView.as_view(), name='register'),

    path('auth/logout/', LogoutView.as_view(), name='logout'),

    path('users/me/', MeView.as_view(), name='me'),

    path('users/me/password/', PasswordChangeView.as_view(), name='password_change'),

    path('users/', UserListCreateView.as_view(), name='user_list'),

    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),

]
