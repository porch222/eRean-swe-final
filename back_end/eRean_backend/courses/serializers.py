import os


from django.conf import settings

from django.urls import reverse

from django.db import transaction

from rest_framework import serializers


from users.serializers import UserSerializer

from .models import (

    ActivityLog,

    Announcement,

    AnnouncementRead,

    Course,

    Curriculum,

    CurriculumCourse,

    Major,

    Material,

    Term,

)


MATERIAL_MAX_SIZE_MB = settings.MAX_MATERIAL_UPLOAD_MB

ALLOWED_MATERIAL_EXTENSIONS = {'.pdf', '.mp4', '.mpeg', '.mov', '.avi'}


EXTENSIONS_BY_TYPE = {

    Material.PDF: {'.pdf'},

    Material.VIDEO: {'.mp4', '.mpeg', '.mov', '.avi'},

}


class MaterialSerializer(serializers.ModelSerializer):


    download_url = serializers.SerializerMethodField()

    filename = serializers.SerializerMethodField()


    file_url = serializers.FileField(write_only=True, required=False, allow_null=True)


    class Meta:

        model = Material

        fields = [

            'id', 'course', 'title', 'type', 'file_url', 'link_url',

            'download_url', 'filename', 'uploaded_at',

        ]

        read_only_fields = ['course', 'uploaded_at']


    def get_download_url(self, obj):

        return reverse(

            'material_download', kwargs={'course_pk': obj.course_id, 'pk': obj.pk}

        )


    def get_filename(self, obj):

        return os.path.basename(obj.file_url.name) if obj.file_url else None


    def validate_file_url(self, value):

        if value:

            size_mb = value.size / (1024 * 1024)

            if size_mb > MATERIAL_MAX_SIZE_MB:

                raise serializers.ValidationError(

                    f'File must not exceed {MATERIAL_MAX_SIZE_MB}MB.'

                )

            ext = os.path.splitext(value.name)[1].lower()

            if ext not in ALLOWED_MATERIAL_EXTENSIONS:

                raise serializers.ValidationError(

                    'Only video (.mp4, .mpeg, .mov, .avi) and PDF files are allowed.'

                )

        return value


    def validate(self, data):

        material_type = data.get('type', getattr(self.instance, 'type', None))

        file_url = data.get('file_url', getattr(self.instance, 'file_url', None))

        link_url = data.get('link_url', getattr(self.instance, 'link_url', None))


        if material_type == Material.LINK:

            if not link_url:

                raise serializers.ValidationError(

                    {'link_url': 'Required for link type materials.'}

                )

            if file_url:

                raise serializers.ValidationError(

                    {'file_url': 'Should not be set for link type materials.'}

                )

        else:

            if not file_url:

                raise serializers.ValidationError(

                    {'file_url': 'Required for video/pdf type materials.'}

                )

            if link_url:

                raise serializers.ValidationError(

                    {'link_url': 'Should not be set for video/pdf type materials.'}

                )


            expected = EXTENSIONS_BY_TYPE.get(material_type, set())

            if hasattr(file_url, 'name') and data.get('file_url') is not None:

                ext = os.path.splitext(file_url.name)[1].lower()

                if expected and ext not in expected:

                    raise serializers.ValidationError(

                        {'file_url': f'A "{material_type}" material must be one of: '

                                     f'{", ".join(sorted(expected))}.'}

                    )


        return data


class TermSerializer(serializers.ModelSerializer):

    course_count = serializers.IntegerField(read_only=True)

    is_open = serializers.BooleanField(read_only=True)


    is_current = serializers.BooleanField(required=False)


    class Meta:

        model = Term

        fields = [

            'id', 'code', 'name', 'year', 'starts_on', 'ends_on',

            'is_current', 'is_open', 'course_count',

        ]


        validators = []


    def _demote_others(self, term):

        Term.objects.exclude(pk=term.pk).update(is_current=False)


    @transaction.atomic

    def create(self, validated_data):

        term = super().create(validated_data)

        if term.is_current:

            self._demote_others(term)

        return term


    @transaction.atomic

    def update(self, instance, validated_data):


        if validated_data.get('is_current'):

            Term.objects.exclude(pk=instance.pk).update(is_current=False)

        return super().update(instance, validated_data)


    def validate(self, attrs):

        starts = attrs.get('starts_on', getattr(self.instance, 'starts_on', None))

        ends = attrs.get('ends_on', getattr(self.instance, 'ends_on', None))

        if starts and ends and ends <= starts:

            raise serializers.ValidationError(

                {'ends_on': 'A term has to end after it starts.'}

            )

        return attrs


class MajorSerializer(serializers.ModelSerializer):

    course_count = serializers.IntegerField(read_only=True)


    class Meta:

        model = Major

        fields = ['id', 'code', 'name', 'description', 'course_count']


class CurriculumCourseSerializer(serializers.ModelSerializer):


    course_title = serializers.CharField(source='course.title', read_only=True)

    course_credits = serializers.IntegerField(source='course.credits', read_only=True)

    course_status = serializers.CharField(source='course.status', read_only=True)


    class Meta:

        model = CurriculumCourse

        fields = [

            'id', 'curriculum', 'course', 'course_title', 'course_credits',

            'course_status', 'year_level', 'term', 'is_required',

        ]


        read_only_fields = ['curriculum']


    def validate(self, attrs):

        curriculum = self.context.get('curriculum') or getattr(self.instance, 'curriculum', None)

        course = attrs.get('course') or getattr(self.instance, 'course', None)

        clash = CurriculumCourse.objects.filter(curriculum=curriculum, course=course)

        if self.instance:

            clash = clash.exclude(pk=self.instance.pk)

        if clash.exists():

            raise serializers.ValidationError('That course is already in this curriculum.')

        return attrs


class CurriculumSerializer(serializers.ModelSerializer):

    major_detail = MajorSerializer(source='major', read_only=True)

    entries = CurriculumCourseSerializer(many=True, read_only=True)

    total_credits = serializers.IntegerField(read_only=True)

    course_count = serializers.IntegerField(source='entries.count', read_only=True)


    graduation_credits = serializers.IntegerField(read_only=True)


    class Meta:

        model = Curriculum

        fields = [

            'id', 'major', 'major_detail', 'name', 'year', 'is_active',

            'credits_to_graduate', 'graduation_credits',

            'entries', 'course_count', 'total_credits',

        ]


    def validate_credits_to_graduate(self, value):


        if value is None:

            return value

        instance = self.instance

        required = instance.total_credits if instance else 0

        if required and value < required:

            raise serializers.ValidationError(

                f'This curriculum already requires {required} credits of '

                f'required courses, so the degree cannot need fewer.'

            )

        return value


class CourseSerializer(serializers.ModelSerializer):

    instructor = serializers.PrimaryKeyRelatedField(read_only=True)

    instructor_detail = UserSerializer(source='instructor', read_only=True)

    material_count = serializers.IntegerField(read_only=True)

    assignment_count = serializers.IntegerField(read_only=True)

    enrolled_count = serializers.IntegerField(read_only=True)

    my_enrollment = serializers.SerializerMethodField()

    major_detail = MajorSerializer(source='major', read_only=True)

    term_detail = TermSerializer(source='term', read_only=True)


    class Meta:

        model = Course

        fields = [

            'id', 'title', 'description', 'major', 'major_detail', 'credits',

            'term', 'term_detail',

            'instructor', 'instructor_detail', 'status', 'created_at',

            'material_count', 'assignment_count', 'enrolled_count', 'my_enrollment',

        ]

        read_only_fields = ['created_at', 'instructor', 'status']


    def get_my_enrollment(self, obj):


        request = self.context.get('request')

        if not request or not request.user.is_authenticated or not request.user.is_student:

            return None

        enrollment = obj.enrollments.filter(student=request.user).first()

        if not enrollment:

            return None

        return {

            'id': enrollment.id,

            'status': enrollment.status,

            'progress': str(enrollment.progress),

        }


class CourseDetailSerializer(CourseSerializer):


    materials = MaterialSerializer(many=True, read_only=True)


    class Meta(CourseSerializer.Meta):

        fields = CourseSerializer.Meta.fields + ['materials']


class CourseApprovalSerializer(serializers.ModelSerializer):

    class Meta:

        model = Course

        fields = ['status']


    def validate_status(self, value):

        if value not in (Course.PUBLISHED, Course.ARCHIVED):

            raise serializers.ValidationError(

                'Admin approval status must be published or archived.'

            )

        return value


class AnnouncementSerializer(serializers.ModelSerializer):

    author = serializers.PrimaryKeyRelatedField(read_only=True)

    author_detail = UserSerializer(source='author', read_only=True)

    is_read = serializers.SerializerMethodField()

    is_edited = serializers.BooleanField(read_only=True)


    class Meta:

        model = Announcement

        fields = [

            'id', 'course', 'author', 'author_detail',

            'title', 'content', 'created_at', 'edited_at', 'is_edited',

            'is_read',

        ]

        read_only_fields = ['course', 'author', 'created_at', 'edited_at']


    def get_is_read(self, obj):

        request = self.context.get('request')

        if not request or not request.user.is_authenticated:

            return False

        return AnnouncementRead.objects.filter(

            announcement=obj, student=request.user

        ).exists()


class AnnouncementReadSerializer(serializers.ModelSerializer):

    class Meta:

        model = AnnouncementRead

        fields = ['id', 'announcement', 'student', 'read_at']

        read_only_fields = fields


class ActivityLogSerializer(serializers.ModelSerializer):

    actor = serializers.PrimaryKeyRelatedField(read_only=True)

    actor_username = serializers.CharField(source='actor.username', read_only=True, default=None)


    class Meta:

        model = ActivityLog

        fields = [

            'id', 'actor', 'actor_username', 'action',

            'target_type', 'target_id', 'details', 'created_at',

        ]

        read_only_fields = fields


class CoursePerformanceSerializer(serializers.Serializer):

    course = serializers.IntegerField()

    students_enrolled = serializers.IntegerField()

    assignments = serializers.IntegerField()

    submissions = serializers.IntegerField()

    graded_submissions = serializers.IntegerField()

    average_progress = serializers.DecimalField(max_digits=5, decimal_places=2)

    average_grade = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
