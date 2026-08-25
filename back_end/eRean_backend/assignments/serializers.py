import os


from django.conf import settings

from django.db import models, transaction

from django.utils import timezone

from rest_framework import serializers


from users.serializers import UserSerializer

from .models import (

    Assignment,

    QuizAnswer,

    QuizAttempt,

    QuizChoice,

    QuizQuestion,

    Submission,

)


ALLOWED_SUBMISSION_EXTENSIONS = {

    '.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.zip',

}

SUBMISSION_MAX_SIZE_MB = settings.MAX_SUBMISSION_UPLOAD_MB


class AssignmentSerializer(serializers.ModelSerializer):

    question_count = serializers.IntegerField(source='questions.count', read_only=True)

    submission_count = serializers.IntegerField(source='submissions.count', read_only=True)

    is_past_due = serializers.SerializerMethodField()


    class Meta:

        model = Assignment

        fields = [

            'id', 'course', 'title', 'description', 'type', 'due_date',

            'max_score', 'created_at', 'question_count', 'submission_count',

            'is_past_due',

        ]

        read_only_fields = ['course', 'created_at']


    def get_is_past_due(self, obj):

        return bool(obj.due_date and obj.due_date < timezone.now())


    def validate(self, attrs):


        assignment = self.instance

        if assignment is None:

            return attrs


        new_type = attrs.get('type', assignment.type)

        if new_type != assignment.type:

            blockers = []

            if assignment.submissions.exists():

                blockers.append('submissions')

            if assignment.quiz_attempts.exists():

                blockers.append('quiz attempts')

            if assignment.questions.exists():

                blockers.append('questions')

            if blockers:

                raise serializers.ValidationError({

                    'type': (

                        'This already has '

                        + ' and '.join(blockers)

                        + ', so its type cannot change. Everything else here '

                          'can still be edited.'

                    )

                })


        new_max = attrs.get('max_score', assignment.max_score)

        if new_max < assignment.max_score:

            highest = assignment.submissions.aggregate(

                top=models.Max('grade')

            )['top']

            if highest is not None and highest > new_max:

                raise serializers.ValidationError({

                    'max_score': (

                        f'A mark of {highest:g} has already been awarded here, '

                        f'so the maximum cannot drop below it. Regrade first '

                        f'if the total really needs to change.'

                    )

                })


        return attrs


class QuizChoiceSerializer(serializers.ModelSerializer):


    class Meta:

        model = QuizChoice

        fields = ['id', 'question', 'text', 'is_correct', 'order']

        read_only_fields = ['question']


class StudentQuizChoiceSerializer(serializers.ModelSerializer):


    class Meta:

        model = QuizChoice

        fields = ['id', 'text', 'order']


class QuizQuestionSerializer(serializers.ModelSerializer):

    choices = QuizChoiceSerializer(many=True, read_only=True)


    class Meta:

        model = QuizQuestion

        fields = ['id', 'assignment', 'text', 'type', 'points', 'order', 'choices']

        read_only_fields = ['assignment']


class StudentQuizQuestionSerializer(serializers.ModelSerializer):

    choices = StudentQuizChoiceSerializer(many=True, read_only=True)


    class Meta:

        model = QuizQuestion

        fields = ['id', 'text', 'type', 'points', 'order', 'choices']


class QuizAnswerSerializer(serializers.ModelSerializer):


    question_text = serializers.CharField(source='question.text', read_only=True)

    question_type = serializers.CharField(source='question.type', read_only=True)

    question_points = serializers.IntegerField(source='question.points', read_only=True)

    student_name = serializers.SerializerMethodField()


    class Meta:

        model = QuizAnswer

        fields = [

            'id', 'question', 'question_text', 'question_type', 'question_points',

            'student_name', 'selected_choice', 'text_answer',

            'is_correct', 'awarded_points',

        ]

        read_only_fields = ['is_correct', 'awarded_points']


    def get_student_name(self, obj):

        student = obj.attempt.student

        return student.get_full_name() or student.username


class QuizAttemptSerializer(serializers.ModelSerializer):

    answers = QuizAnswerSerializer(many=True, read_only=True)

    student_detail = UserSerializer(source='student', read_only=True)


    class Meta:

        model = QuizAttempt

        fields = [

            'id', 'assignment', 'student', 'student_detail', 'score',

            'needs_manual_grading', 'graded_at', 'submitted_at', 'answers',

        ]

        read_only_fields = fields


class QuizAnswerInputSerializer(serializers.Serializer):


    question = serializers.IntegerField()

    selected_choice = serializers.IntegerField(required=False, allow_null=True)

    selected_choices = serializers.ListField(

        child=serializers.IntegerField(), required=False, allow_empty=True

    )

    text_answer = serializers.CharField(required=False, allow_blank=True, default='')


class GradeWrittenAnswerSerializer(serializers.Serializer):


    awarded_points = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)

    def validate(self, attrs):

        answer = self.context.get('answer')

        if answer and attrs['awarded_points'] > answer.question.points:

            raise serializers.ValidationError(

                f'That question is worth at most {answer.question.points} points.'

            )

        return attrs


class QuizAttemptCreateSerializer(serializers.Serializer):


    answers = QuizAnswerInputSerializer(many=True, allow_empty=False)


    def validate(self, data):

        request = self.context['request']

        view = self.context['view']

        assignment = Assignment.objects.filter(

            pk=view.kwargs.get('assignment_pk'),

            course_id=view.kwargs.get('course_pk'),

            type=Assignment.QUIZ,

        ).first()


        if not assignment:

            raise serializers.ValidationError('Quiz does not exist.')

        if assignment.due_date and assignment.due_date < timezone.now():

            raise serializers.ValidationError('This quiz is past its due date.')

        if QuizAttempt.objects.filter(assignment=assignment, student=request.user).exists():

            raise serializers.ValidationError('You have already submitted this quiz.')

        if Submission.objects.filter(assignment=assignment, student=request.user).exists():

            raise serializers.ValidationError('You already have a submission for this quiz.')

        if not assignment.course.enrollments.filter(

            student=request.user, status='active'

        ).exists():

            raise serializers.ValidationError(

                'You must be actively enrolled in this course before taking the quiz.'

            )


        answers = data['answers']

        question_ids = [answer['question'] for answer in answers]

        if len(question_ids) != len(set(question_ids)):

            raise serializers.ValidationError('Each question can only be answered once.')


        questions = QuizQuestion.objects.filter(assignment=assignment, id__in=question_ids)

        if questions.count() != len(question_ids):

            raise serializers.ValidationError('One or more questions are invalid.')

        questions_by_id = {q.id: q for q in questions}


        choices_by_id = {

            choice.id: choice

            for choice in QuizChoice.objects.filter(

                question__assignment=assignment, question_id__in=question_ids

            ).select_related('question')

        }


        for answer in answers:

            question = questions_by_id[answer['question']]

            chosen = self._chosen_ids(answer)


            if question.type == QuizQuestion.WRITTEN:

                if chosen:

                    raise serializers.ValidationError(

                        'A written question takes text, not a choice.'

                    )

                continue


            if not chosen:

                raise serializers.ValidationError(

                    f'Question {question.id} needs an answer.'

                )

            if question.type != QuizQuestion.MULTIPLE and len(chosen) > 1:

                raise serializers.ValidationError(

                    'That question only takes one answer.'

                )

            for choice_id in chosen:

                choice = choices_by_id.get(choice_id)

                if not choice or choice.question_id != question.id:

                    raise serializers.ValidationError(

                        'One or more selected choices are invalid.'

                    )


        data['assignment'] = assignment

        data['choices_by_id'] = choices_by_id

        data['questions_by_id'] = questions_by_id

        return data


    @staticmethod

    def _chosen_ids(answer):


        if answer.get('selected_choices'):

            return list(answer['selected_choices'])

        if answer.get('selected_choice'):

            return [answer['selected_choice']]

        return []


    @transaction.atomic

    def create(self, validated_data):


        request = self.context['request']

        assignment = validated_data['assignment']

        choices_by_id = validated_data['choices_by_id']


        questions_by_id = validated_data['questions_by_id']


        attempt = QuizAttempt.objects.create(assignment=assignment, student=request.user)

        score = 0

        pending = False


        for answer in validated_data['answers']:

            question = questions_by_id[answer['question']]


            if question.type == QuizQuestion.WRITTEN:


                QuizAnswer.objects.create(

                    attempt=attempt,

                    question=question,

                    selected_choice=None,

                    text_answer=answer.get('text_answer', ''),

                    is_correct=False,

                )

                pending = True

                continue


            chosen = self._chosen_ids(answer)


            if question.type == QuizQuestion.MULTIPLE:

                correct = {

                    c.id for c in choices_by_id.values()

                    if c.question_id == question.id and c.is_correct

                }


                got_it = bool(correct) and set(chosen) == correct

                if got_it:

                    score += question.points

                for choice_id in chosen:

                    QuizAnswer.objects.create(

                        attempt=attempt,

                        question=question,

                        selected_choice=choices_by_id[choice_id],

                        is_correct=got_it,

                    )

            else:

                choice = choices_by_id[chosen[0]]

                if choice.is_correct:

                    score += question.points

                QuizAnswer.objects.create(

                    attempt=attempt,

                    question=question,

                    selected_choice=choice,

                    is_correct=choice.is_correct,

                )


        attempt.score = min(score, assignment.max_score)

        attempt.needs_manual_grading = pending

        attempt.save(update_fields=['score', 'needs_manual_grading'])


        Submission.objects.create(

            assignment=assignment,

            student=request.user,

            grade=None if pending else attempt.score,

            feedback=(

                'Submitted — awaiting marking of the written answers.'

                if pending else 'Auto-graded quiz submission.'

            ),

        )

        return attempt


class SubmissionSerializer(serializers.ModelSerializer):

    student = serializers.PrimaryKeyRelatedField(read_only=True)

    student_detail = UserSerializer(source='student', read_only=True)

    assignment_title = serializers.CharField(source='assignment.title', read_only=True)

    assignment_type = serializers.CharField(source='assignment.type', read_only=True)

    max_score = serializers.IntegerField(source='assignment.max_score', read_only=True)

    course = serializers.IntegerField(source='assignment.course_id', read_only=True)

    course_title = serializers.CharField(source='assignment.course.title', read_only=True)

    course_category = serializers.CharField(

        source='assignment.course.major.name', read_only=True, default=None

    )

    download_url = serializers.SerializerMethodField()

    filename = serializers.SerializerMethodField()

    is_graded = serializers.BooleanField(read_only=True)


    file_url = serializers.FileField(write_only=True, required=False, allow_null=True)


    class Meta:

        model = Submission

        fields = [

            'id', 'assignment', 'assignment_title', 'assignment_type', 'max_score',

            'course', 'course_title', 'course_category', 'student', 'student_detail', 'file_url',

            'download_url', 'filename', 'grade', 'feedback', 'is_graded',

            'attempt', 'is_latest', 'is_late',

            'submitted_at',

        ]

        read_only_fields = [

            'assignment', 'submitted_at', 'student', 'grade', 'feedback',

        ]


    def get_download_url(self, obj):

        if not obj.file_url:

            return None

        return (

            f'/api/courses/{obj.assignment.course_id}/assignments/'

            f'{obj.assignment_id}/submissions/{obj.pk}/download/'

        )


    def get_filename(self, obj):

        return os.path.basename(obj.file_url.name) if obj.file_url else None


    def validate_file_url(self, value):

        if value:

            size_mb = value.size / (1024 * 1024)

            if size_mb > SUBMISSION_MAX_SIZE_MB:

                raise serializers.ValidationError(

                    f'Submission file must not exceed {SUBMISSION_MAX_SIZE_MB}MB.'

                )

            ext = os.path.splitext(value.name)[1].lower()

            if ext not in ALLOWED_SUBMISSION_EXTENSIONS:

                raise serializers.ValidationError('Unsupported submission file type.')

        return value


    def validate(self, data):

        request = self.context.get('request')

        view = self.context.get('view')

        if not request or not view or not request.user.is_authenticated:

            return data


        assignment = Assignment.objects.filter(

            pk=view.kwargs.get('assignment_pk'),

            course_id=view.kwargs.get('course_pk'),

        ).select_related('course').first()

        if not assignment:

            raise serializers.ValidationError('Assignment does not exist.')


        if assignment.type == Assignment.QUIZ:

            raise serializers.ValidationError(

                'This is a quiz. Submit your answers through the quiz attempt endpoint.'

            )


        if not data.get('file_url') and not getattr(self.instance, 'file_url', None):

            raise serializers.ValidationError({'file_url': 'A file is required.'})


        if not assignment.course.enrollments.filter(

            student=request.user, status='active'

        ).exists():

            raise serializers.ValidationError(

                'You must be actively enrolled in this course before submitting.'

            )


        return data


class GradeSubmissionSerializer(serializers.ModelSerializer):

    class Meta:

        model = Submission

        fields = ['grade', 'feedback']


    def validate_grade(self, value):

        if value is None:

            return value

        if value < 0:

            raise serializers.ValidationError('Grade cannot be negative.')

        max_score = self.instance.assignment.max_score

        if value > max_score:

            raise serializers.ValidationError(

                f'Grade cannot exceed the maximum score of {max_score}.'

            )

        return value
