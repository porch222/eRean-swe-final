from rest_framework import serializers


from users.serializers import UserSerializer

from .models import Reply, Thread


class ReplySerializer(serializers.ModelSerializer):

    author = serializers.PrimaryKeyRelatedField(read_only=True)

    author_detail = UserSerializer(source='author', read_only=True)


    class Meta:

        model = Reply

        fields = [

            'id', 'thread', 'author', 'author_detail', 'body',

            'is_answer', 'created_at', 'updated_at',

        ]


        read_only_fields = ['id', 'thread', 'author', 'is_answer', 'created_at', 'updated_at']


class ThreadSerializer(serializers.ModelSerializer):

    author = serializers.PrimaryKeyRelatedField(read_only=True)

    author_detail = UserSerializer(source='author', read_only=True)

    reply_count = serializers.IntegerField(read_only=True)

    is_answered = serializers.BooleanField(read_only=True)


    class Meta:

        model = Thread

        fields = [

            'id', 'course', 'author', 'author_detail', 'kind', 'title', 'body',

            'is_pinned', 'is_locked', 'is_answered', 'reply_count',

            'created_at', 'updated_at',

        ]


        read_only_fields = [

            'id', 'course', 'author', 'is_pinned', 'is_locked', 'created_at', 'updated_at',

        ]


class ThreadDetailSerializer(ThreadSerializer):

    replies = ReplySerializer(many=True, read_only=True)


    class Meta(ThreadSerializer.Meta):

        fields = ThreadSerializer.Meta.fields + ['replies']


class ModerateThreadSerializer(serializers.ModelSerializer):


    class Meta:

        model = Thread

        fields = ['is_pinned', 'is_locked']
