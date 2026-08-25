from django.contrib import admin

from .models import Assignment, QuizAnswer, QuizAttempt, QuizChoice, QuizQuestion, Submission


admin.site.register(Assignment)

admin.site.register(Submission)

admin.site.register(QuizQuestion)

admin.site.register(QuizChoice)

admin.site.register(QuizAttempt)

admin.site.register(QuizAnswer)
