from rest_framework import serializers


from .models import AttendanceRecord, AttendanceSession


class AttendanceRecordSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    student_username = serializers.CharField(source='student.username', read_only=True)


    class Meta:

        model = AttendanceRecord

        fields = [

            'id', 'session', 'student', 'student_name', 'student_username',

            'status', 'note',

        ]

        read_only_fields = ['id', 'session']


class AttendanceSessionSerializer(serializers.ModelSerializer):

    records = AttendanceRecordSerializer(many=True, read_only=True)

    present_count = serializers.SerializerMethodField()

    total_count = serializers.SerializerMethodField()


    class Meta:

        model = AttendanceSession

        fields = [

            'id', 'course', 'date', 'title', 'created_at',

            'records', 'present_count', 'total_count',

        ]

        read_only_fields = ['id', 'course', 'created_at']


    def get_present_count(self, obj):

        return sum(1 for r in obj.records.all() if r.counts_as_attended)


    def get_total_count(self, obj):

        return obj.records.count()


class MarkAttendanceSerializer(serializers.Serializer):


    records = serializers.ListField(child=serializers.DictField(), allow_empty=False)


    def validate_records(self, value):

        valid = {choice for choice, _ in AttendanceRecord.STATUS_CHOICES}

        for row in value:

            if 'student' not in row:

                raise serializers.ValidationError('Each row needs a student.')

            status = row.get('status', AttendanceRecord.PRESENT)

            if status not in valid:

                raise serializers.ValidationError(f'"{status}" is not a valid status.')

        return value
