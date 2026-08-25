from rest_framework import serializers


from courses.models import Course

from users.serializers import UserSerializer

from .models import DropRequest, Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):


    student = serializers.PrimaryKeyRelatedField(read_only=True)

    student_detail = UserSerializer(source='student', read_only=True)

    course_title = serializers.CharField(source='course.title', read_only=True)

    course_status = serializers.CharField(source='course.status', read_only=True)

    course_credits = serializers.IntegerField(source='course.credits', read_only=True)

    is_passed = serializers.BooleanField(read_only=True)


    class Meta:

        model = Enrollment

        fields = [

            'id', 'student', 'student_detail', 'course', 'course_title',

            'course_status', 'status', 'progress', 'enrolled_at',

            'final_score', 'letter_grade', 'credits_earned', 'finalized_at',

            'is_passed', 'course_credits',

        ]

        read_only_fields = [

            'enrolled_at', 'student', 'progress',

            'final_score', 'letter_grade', 'credits_earned', 'finalized_at',

        ]


    def validate(self, data):


        if self.instance:

            student = self.instance.student

        else:

            request = self.context.get('request')

            student = getattr(request, 'user', None)


        course = data.get('course', getattr(self.instance, 'course', None))

        if not student or not course:

            return data


        if student.is_student and course.status != Course.PUBLISHED:

            raise serializers.ValidationError(

                'Cannot enroll in a course that is not published.'

            )


        duplicate = Enrollment.objects.filter(student=student, course=course)

        if self.instance:

            duplicate = duplicate.exclude(pk=self.instance.pk)

        if duplicate.exists():

            raise serializers.ValidationError('You are already enrolled in this course.')


        return data


class StudentEnrollmentSerializer(EnrollmentSerializer):


    class Meta(EnrollmentSerializer.Meta):

        read_only_fields = EnrollmentSerializer.Meta.read_only_fields + ['course', 'status']


class DropRequestSerializer(serializers.ModelSerializer):

    student_detail = UserSerializer(source='enrollment.student', read_only=True)

    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)

    course = serializers.IntegerField(source='enrollment.course_id', read_only=True)

    decided_by_name = serializers.CharField(

        source='decided_by.get_full_name', read_only=True, default=''

    )


    class Meta:

        model = DropRequest

        fields = [

            'id', 'enrollment', 'student_detail', 'course', 'course_title',

            'reason', 'status', 'decided_by', 'decided_by_name', 'decision_note',

            'created_at', 'decided_at',

        ]

        read_only_fields = [

            'id', 'status', 'decided_by', 'decision_note', 'created_at', 'decided_at',

        ]


    def validate_enrollment(self, enrollment):

        request = self.context.get('request')

        user = getattr(request, 'user', None)

        if user and user.is_student and enrollment.student_id != user.id:

            raise serializers.ValidationError('This is not your enrollment.')

        if enrollment.status != Enrollment.ACTIVE:

            raise serializers.ValidationError('That enrollment is not active.')

        if enrollment.drop_requests.filter(status=DropRequest.PENDING).exists():

            raise serializers.ValidationError(

                'You already have a drop request waiting on a decision.'

            )

        return enrollment


class DropDecisionSerializer(serializers.Serializer):


    status = serializers.ChoiceField(choices=[DropRequest.APPROVED, DropRequest.REJECTED])

    decision_note = serializers.CharField(required=False, allow_blank=True, default='')
