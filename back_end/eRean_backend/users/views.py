from django.db.models import Q

from rest_framework import generics, permissions, status

from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework.response import Response

from rest_framework.throttling import ScopedRateThrottle

from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.views import TokenObtainPairView


from .models import User

from .permissions import IsAdmin

from .serializers import (

    AdminUserCreateSerializer,

    PasswordChangeSerializer,

    ProfileSerializer,

    RegisterSerializer,

    UserSerializer,

)


class LoginTokenSerializer(TokenObtainPairSerializer):


    def validate(self, attrs):

        data = super().validate(attrs)

        data['user'] = UserSerializer(self.user).data

        return data


class LoginView(TokenObtainPairView):

    serializer_class = LoginTokenSerializer

    throttle_classes = [ScopedRateThrottle]

    throttle_scope = 'login'


class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()

    serializer_class = RegisterSerializer

    permission_classes = [permissions.AllowAny]

    throttle_classes = [ScopedRateThrottle]

    throttle_scope = 'register'


class LogoutView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def post(self, request):

        refresh = request.data.get('refresh')

        if not refresh:

            raise ValidationError({'refresh': ['This field is required.']})

        try:

            RefreshToken(refresh).blacklist()

        except TokenError:


            pass

        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):


    permission_classes = [permissions.IsAuthenticated]


    def get(self, request):

        return Response(ProfileSerializer(request.user).data)


    def patch(self, request):

        serializer = ProfileSerializer(request.user, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)


    def put(self, request):

        return self.patch(request)


class PasswordChangeView(APIView):

    permission_classes = [permissions.IsAuthenticated]


    def post(self, request):

        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({'detail': 'Password updated.'})


class UserListCreateView(generics.ListCreateAPIView):


    permission_classes = [IsAdmin]

    search_fields = ['username', 'email', 'first_name', 'last_name']

    ordering_fields = ['username', 'date_joined', 'role']

    ordering = ['username']

    filterset_fields = ['role', 'is_active']


    def get_serializer_class(self):

        if self.request.method == 'POST':

            return AdminUserCreateSerializer

        return UserSerializer


    def get_queryset(self):

        queryset = User.objects.all()

        role = self.request.query_params.get('role')

        if role:

            queryset = queryset.filter(role=role)

        return queryset


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = User.objects.all()

    serializer_class = UserSerializer

    permission_classes = [IsAdmin]


    def perform_update(self, serializer):

        target = self.get_object()

        new_role = serializer.validated_data.get('role', target.role)


        if target == self.request.user and new_role != User.ADMIN:

            raise PermissionDenied('You cannot change your own role.')

        if target.is_admin and new_role != User.ADMIN and self._last_admin(target):

            raise PermissionDenied('At least one admin account must remain.')

        serializer.save()


    def perform_destroy(self, instance):

        if instance == self.request.user:

            raise PermissionDenied('You cannot delete your own account.')

        if instance.is_admin and self._last_admin(instance):

            raise PermissionDenied('At least one admin account must remain.')

        instance.delete()


    @staticmethod

    def _last_admin(user):

        return not User.objects.filter(Q(role=User.ADMIN) & ~Q(pk=user.pk)).exists()
