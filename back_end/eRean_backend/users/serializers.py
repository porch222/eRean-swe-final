from django.contrib.auth.password_validation import validate_password

from django.core.exceptions import ValidationError as DjangoValidationError

from django.db import IntegrityError

from rest_framework import serializers


from courses.models import Major

from .models import User


class MajorBriefSerializer(serializers.ModelSerializer):


    class Meta:

        model = Major

        fields = ['id', 'code', 'name']


class UserSerializer(serializers.ModelSerializer):


    full_name = serializers.CharField(read_only=True)

    major_detail = MajorBriefSerializer(source='major', read_only=True)


    class Meta:

        model = User

        fields = [

            'id', 'username', 'email', 'first_name', 'last_name',

            'full_name', 'role', 'major', 'major_detail', 'is_active', 'date_joined',

        ]

        read_only_fields = ['id', 'date_joined']


class ProfileSerializer(serializers.ModelSerializer):


    full_name = serializers.CharField(read_only=True)

    major_detail = MajorBriefSerializer(source='major', read_only=True)


    class Meta:

        model = User

        fields = [

            'id', 'username', 'email', 'first_name', 'last_name',

            'full_name', 'role', 'major', 'major_detail', 'date_joined',

        ]


        read_only_fields = ['id', 'username', 'role', 'major', 'date_joined']


    def validate_email(self, value):

        if value and User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():

            raise serializers.ValidationError('This email is already in use.')

        return value


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})


    class Meta:

        model = User

        fields = [

            'username', 'email', 'password', 'password_confirm',

            'first_name', 'last_name',

        ]

        extra_kwargs = {


            'username': {'validators': []},

            'email': {'required': True, 'allow_blank': False},

        }


    def validate_username(self, value):

        if User.objects.filter(username__iexact=value).exists():

            raise serializers.ValidationError('Unable to register with these credentials.')

        return value


    def validate_email(self, value):

        if User.objects.filter(email__iexact=value).exists():

            raise serializers.ValidationError('Unable to register with these credentials.')

        return value


    def validate(self, data):

        if data.get('password') != data.get('password_confirm'):

            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})


        candidate = User(

            username=data.get('username', ''),

            email=data.get('email', ''),

            first_name=data.get('first_name', ''),

            last_name=data.get('last_name', ''),

        )

        try:

            validate_password(data.get('password'), user=candidate)

        except DjangoValidationError as exc:

            raise serializers.ValidationError({'password': list(exc.messages)})

        return data


    def create(self, validated_data):

        validated_data.pop('password_confirm', None)

        try:

            return User.objects.create_user(

                username=validated_data['username'],

                email=validated_data.get('email', ''),

                password=validated_data['password'],

                first_name=validated_data.get('first_name', ''),

                last_name=validated_data.get('last_name', ''),


                role=User.STUDENT,

            )

        except IntegrityError:


            raise serializers.ValidationError(

                {'username': ['Unable to register with these credentials.']}

            )


class PasswordChangeSerializer(serializers.Serializer):

    current_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    new_password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})


    def validate_current_password(self, value):

        user = self.context['request'].user

        if not user.check_password(value):

            raise serializers.ValidationError('Current password is incorrect.')

        return value


    def validate(self, data):

        if data['new_password'] != data['new_password_confirm']:

            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})

        user = self.context['request'].user

        try:

            validate_password(data['new_password'], user=user)

        except DjangoValidationError as exc:

            raise serializers.ValidationError({'new_password': list(exc.messages)})

        return data


    def save(self, **kwargs):

        user = self.context['request'].user

        user.set_password(self.validated_data['new_password'])

        user.save(update_fields=['password'])

        return user


class AdminUserCreateSerializer(serializers.ModelSerializer):


    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


    class Meta:

        model = User

        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'role']


    def validate(self, data):

        candidate = User(username=data.get('username', ''), email=data.get('email', ''))

        try:

            validate_password(data.get('password'), user=candidate)

        except DjangoValidationError as exc:

            raise serializers.ValidationError({'password': list(exc.messages)})

        return data


    def create(self, validated_data):

        password = validated_data.pop('password')

        user = User(**validated_data)

        user.set_password(password)

        user.save()

        return user
