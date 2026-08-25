from django.urls import path


from .views import (

    AssignmentDetailView,

    AssignmentListCreateView,

    GradeWrittenAnswerView,

    PendingWrittenAnswersView,

    QuizAttemptListCreateView,

    QuizChoiceDetailView,

    QuizChoiceListCreateView,

    QuizQuestionDetailView,

    QuizQuestionListCreateView,

    SubmissionDetailView,

    SubmissionDownloadView,

    SubmissionListCreateView,

)


urlpatterns = [

    path('', AssignmentListCreateView.as_view(), name='assignment_list_create'),

    path('<int:pk>/', AssignmentDetailView.as_view(), name='assignment_detail'),

    path(

        '<int:assignment_pk>/questions/',

        QuizQuestionListCreateView.as_view(),

        name='quiz_question_list_create',

    ),

    path(

        '<int:assignment_pk>/questions/<int:pk>/',

        QuizQuestionDetailView.as_view(),

        name='quiz_question_detail',

    ),

    path(

        '<int:assignment_pk>/questions/<int:question_pk>/choices/',

        QuizChoiceListCreateView.as_view(),

        name='quiz_choice_list_create',

    ),

    path(

        '<int:assignment_pk>/questions/<int:question_pk>/choices/<int:pk>/',

        QuizChoiceDetailView.as_view(),

        name='quiz_choice_detail',

    ),

    path(

        '<int:assignment_pk>/attempts/',

        QuizAttemptListCreateView.as_view(),

        name='quiz_attempt_list_create',

    ),

    path(

        '<int:assignment_pk>/written-answers/',

        PendingWrittenAnswersView.as_view(),

        name='pending_written_answers',

    ),

    path(

        '<int:assignment_pk>/written-answers/<int:pk>/grade/',

        GradeWrittenAnswerView.as_view(),

        name='grade_written_answer',

    ),

    path(

        '<int:assignment_pk>/submissions/',

        SubmissionListCreateView.as_view(),

        name='submission_list_create',

    ),

    path(

        '<int:assignment_pk>/submissions/<int:pk>/',

        SubmissionDetailView.as_view(),

        name='submission_detail',

    ),

    path(

        '<int:assignment_pk>/submissions/<int:pk>/download/',

        SubmissionDownloadView.as_view(),

        name='submission_download',

    ),

]
