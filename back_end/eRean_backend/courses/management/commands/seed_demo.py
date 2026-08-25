from datetime import date, timedelta


from django.contrib.auth import get_user_model

from django.core.files.base import ContentFile

from django.core.management.base import BaseCommand

from django.db import transaction

from django.utils import timezone


from assignments.models import (

    Assignment,

    QuizAnswer,

    QuizAttempt,

    QuizChoice,

    QuizQuestion,

    Submission,

)

from courses.models import (

    ActivityLog,

    Term,

    Announcement,

    AnnouncementRead,

    Course,

    Curriculum,

    CurriculumCourse,

    Major,

    Material,

)

from attendance.models import AttendanceRecord, AttendanceSession

from discussions.models import Reply, Thread

from enrollments.models import DropRequest, Enrollment

from notifications.models import Notification


User = get_user_model()


PASSWORD = 'eRean!Demo2026'


SAMPLE_PDF = (

    b'%PDF-1.4\n'

    b'1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'

    b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'

    b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n'

    b'trailer<</Root 1 0 R>>\n%%EOF\n'

)


class Command(BaseCommand):

    help = 'Populate the database with demo users, courses and coursework.'


    def add_arguments(self, parser):

        parser.add_argument(

            '--reset',

            action='store_true',

            help='Delete all existing courses, enrollments and demo users first.',

        )


    @transaction.atomic

    def handle(self, *args, **options):

        if options['reset']:

            self.stdout.write('Clearing existing data...')

            ActivityLog.objects.all().delete()

            AnnouncementRead.objects.all().delete()

            QuizAnswer.objects.all().delete()

            QuizAttempt.objects.all().delete()

            Submission.objects.all().delete()

            QuizChoice.objects.all().delete()

            QuizQuestion.objects.all().delete()

            Assignment.objects.all().delete()

            Announcement.objects.all().delete()

            Material.objects.all().delete()

            Enrollment.objects.all().delete()

            Notification.objects.all().delete()

            Reply.objects.all().delete()

            Thread.objects.all().delete()

            AttendanceRecord.objects.all().delete()

            AttendanceSession.objects.all().delete()

            DropRequest.objects.all().delete()

            CurriculumCourse.objects.all().delete()

            Curriculum.objects.all().delete()

            Course.objects.all().delete()

            Term.objects.all().delete()

            User.objects.filter(is_superuser=False).delete()


            Major.objects.all().delete()


        now = timezone.now()


        admin = self.make_user('admin', 'Ada', 'Admin', User.ADMIN)

        smith = self.make_user('prof.smith', 'John', 'Smith', User.INSTRUCTOR)

        chen = self.make_user('prof.chen', 'Mei', 'Chen', User.INSTRUCTOR)


        students = [

            self.make_user('alice', 'Alice', 'Nguyen', User.STUDENT),

            self.make_user('bob', 'Bob', 'Martinez', User.STUDENT),

            self.make_user('carla', 'Carla', 'Okafor', User.STUDENT),

            self.make_user('dan', 'Dan', 'Petrov', User.STUDENT),

        ]


        past_term = self.make_term(

            '2025-FA', 'Fall 2025', 2025, date(2025, 8, 25), date(2025, 12, 19), False

        )

        term = self.make_term(

            '2026-FA', 'Fall 2026', 2026, date(2026, 8, 24), date(2026, 12, 18), True

        )


        cs = self.make_major('CS', 'Computer Science',

                             'Software, systems and the theory behind them.')

        math = self.make_major('MATH', 'Mathematics',

                               'Pure and applied mathematics, including statistics.')


        intro = self.make_course(

            'Introduction to Programming',

            'Variables, control flow, functions and a first look at data '

            'structures using Python.',

            cs, smith, Course.PUBLISHED, credits=3, term=term,

        )

        web = self.make_course(

            'Web Development Fundamentals',

            'HTML, CSS, JavaScript and how a browser talks to a REST API.',

            cs, smith, Course.PUBLISHED, credits=4, term=term,

        )

        stats = self.make_course(

            'Statistics for Data Science',

            'Descriptive statistics, probability distributions and hypothesis '

            'testing.',

            math, chen, Course.PUBLISHED, credits=4, term=term,

        )

        pending = self.make_course(

            'Machine Learning Basics',

            'Awaiting admin approval — supervised learning, model evaluation '

            'and overfitting.',

            cs, chen, Course.DRAFT, credits=3, term=term,

        )

        self.make_course(

            'Legacy Systems in COBOL',

            'Retired course, kept for the archive.',

            cs, smith, Course.ARCHIVED, credits=2, term=past_term,

        )


        self.make_curriculum(cs, 'BSCS 2026', 2026, [

            (intro, 1, 1, True),

            (web, 2, 1, True),

            (stats, 2, 2, False),

            (pending, 3, 1, False),

        ], credits_to_graduate=12)

        self.make_curriculum(math, 'BS Mathematics 2026', 2026, [

            (stats, 1, 1, True),

            (intro, 1, 2, False),

        ])


        for student in students[:3]:

            student.major = cs

            student.save(update_fields=['major'])

        students[3].major = math

        students[3].save(update_fields=['major'])


        self.make_file_material(intro, 'Week 1 — Course Handbook')

        self.make_file_material(intro, 'Week 2 — Control Flow Slides')

        self.make_link_material(

            intro, 'Official Python Tutorial', 'https://docs.python.org/3/tutorial/'

        )

        self.make_file_material(web, 'HTTP and REST Primer')

        self.make_link_material(

            web, 'MDN Web Docs', 'https://developer.mozilla.org/'

        )

        self.make_file_material(stats, 'Probability Distributions Notes')


        self.make_announcement(

            intro, smith, 'Welcome to the course',

            'Please read the handbook before the first lab session.',

        )

        self.make_announcement(

            intro, smith, 'Lab rooms changed',

            'Thursday labs move to room B204 starting this week.',

        )

        self.make_announcement(

            stats, chen, 'Office hours',

            'I am available Tuesdays 14:00-16:00 for questions on problem set 1.',

        )


        for student in students[:3]:

            self.enroll(student, intro)

        self.enroll(students[0], web)

        self.enroll(students[1], web)

        self.enroll(students[0], stats)

        self.enroll(students[3], intro, status=Enrollment.DROPPED)


        essay = self.make_assignment(

            intro, 'Assignment 1 — FizzBuzz',

            'Submit a Python file that prints FizzBuzz from 1 to 100.',

            Assignment.ASSIGNMENT, now + timedelta(days=14), 100,

        )

        report = self.make_assignment(

            web, 'Assignment 1 — Static Portfolio Page',

            'Build a single responsive page and submit it as a .zip archive.',

            Assignment.ASSIGNMENT, now + timedelta(days=21), 50,

        )


        quiz = self.make_assignment(

            intro, 'Quiz 1 — Python Basics',

            'Ten minutes, one attempt. Covers weeks 1 and 2.',

            Assignment.QUIZ, now + timedelta(days=7), 30,

        )

        self.make_question(

            quiz, 'Which keyword defines a function in Python?', 10, 0,

            [('def', True), ('func', False), ('function', False), ('lambda', False)],

        )

        self.make_question(

            quiz, 'What is the result of len("hello")?', 10, 1,

            [('4', False), ('5', True), ('6', False), ('Error', False)],

        )

        self.make_question(

            quiz, 'Which type is immutable?', 10, 2,

            [('list', False), ('dict', False), ('tuple', True), ('set', False)],

        )


        stats_quiz = self.make_assignment(

            stats, 'Quiz 1 — Descriptive Statistics',

            'Short check on means, medians and spread.',

            Assignment.QUIZ, now + timedelta(days=10), 20,

        )

        self.make_question(

            stats_quiz, 'Which measure is most affected by outliers?', 10, 0,

            [('Median', False), ('Mean', True), ('Mode', False), ('Range', False)],

        )

        self.make_question(

            stats_quiz, 'The standard deviation is the square root of the...?', 10, 1,

            [('Mean', False), ('Variance', True), ('Median', False), ('Range', False)],

        )


        self.make_submission(essay, students[0], grade=92, feedback='Clean solution, good naming.')

        self.make_submission(essay, students[1], grade=74, feedback='Works, but the loop can be simplified.')

        self.make_submission(essay, students[2])

        self.make_submission(report, students[0], grade=45, feedback='Nice layout. Watch your colour contrast.')


        self.take_quiz(quiz, students[0], correct_ratio=1.0)

        self.take_quiz(quiz, students[1], correct_ratio=0.5)


        self.recompute_progress()


        first_announcement = intro.announcements.order_by('created_at').first()

        if first_announcement:

            AnnouncementRead.objects.get_or_create(

                announcement=first_announcement, student=students[0]

            )


        mixed = self.make_assignment(

            intro, 'Quiz 2 — Mixed formats',

            'Shows all four question types, including a written answer that '

            'has to be marked by hand.',

            Assignment.QUIZ, now + timedelta(days=10), 40,

        )

        self.make_question(

            mixed, 'HTML stands for?', 10, 0,

            [('HyperText Markup Language', True), ('Hyperlink Text Mode', False)],

        )

        self.make_question(

            mixed, 'CSS can control both colour and layout.', 10, 1,

            [('True', True), ('False', False)],

            qtype=QuizQuestion.TRUE_FALSE,

        )

        self.make_question(

            mixed, 'Which of these are HTTP methods?', 10, 2,

            [('GET', True), ('POST', True), ('FETCH', False)],

            qtype=QuizQuestion.MULTIPLE,

        )

        self.make_question(

            mixed, 'In your own words, what is a REST API?', 10, 3, [],

            qtype=QuizQuestion.WRITTEN,

        )


        for offset, label in ((14, 'Week 1'), (7, 'Week 2')):

            session, _ = AttendanceSession.objects.get_or_create(

                course=intro, date=(now - timedelta(days=offset)).date(),

                defaults={'title': label},

            )

            for index, student in enumerate(students[:3]):

                AttendanceRecord.objects.get_or_create(

                    session=session, student=student,

                    defaults={'status': 'absent' if index == 2 else 'present'},

                )


        thread, _ = Thread.objects.get_or_create(

            course=intro, author=students[0],

            title='Study group for the quiz?',

            defaults={'body': 'Anyone want to revise together before Friday?'},

        )

        Reply.objects.get_or_create(

            thread=thread, author=students[1], defaults={'body': 'Count me in.'}

        )

        question_thread, _ = Thread.objects.get_or_create(

            course=intro, author=students[1],

            title='Why does my loop print one extra line?',

            defaults={

                'body': 'My FizzBuzz prints 101 lines. What am I missing?',

                'kind': Thread.QUESTION,

            },

        )

        Reply.objects.get_or_create(

            thread=question_thread, author=smith,

            defaults={

                'body': 'range(1, 101) stops at 100 — check your upper bound.',

                'is_answer': True,

            },

        )


        finished = Enrollment.objects.filter(student=students[0], course=web).first()

        if finished and not finished.finalized_at:

            finished.finalize()


        dropper = Enrollment.objects.filter(student=students[2], course=intro).first()

        if dropper and dropper.status == Enrollment.ACTIVE:

            DropRequest.objects.get_or_create(

                enrollment=dropper,

                defaults={'reason': 'Clashes with my part-time job.'},

            )


        self.report(admin, smith, chen, students, pending)


    def make_user(self, username, first, last, role):

        user = User.objects.filter(username=username).first()

        if user:

            return user

        user = User.objects.create_user(

            username=username,

            email=f'{username}@erean.test',

            password=PASSWORD,

            first_name=first,

            last_name=last,

            role=role,

        )

        if role == User.ADMIN:


            user.is_staff = True

            user.is_superuser = True

            user.save(update_fields=['is_staff', 'is_superuser'])

        return user


    def make_course(self, title, description, major, instructor, status,

                    credits=3, term=None):

        course, _ = Course.objects.get_or_create(

            title=title,

            defaults={

                'description': description,

                'major': major,

                'credits': credits,

                'term': term,

                'instructor': instructor,

                'status': status,

            },

        )

        return course


    def make_term(self, code, name, year, starts, ends, is_current):

        term, _ = Term.objects.get_or_create(

            code=code,

            defaults={

                'name': name, 'year': year, 'starts_on': starts,

                'ends_on': ends, 'is_current': is_current,

            },

        )

        return term


    def make_major(self, code, name, description=''):

        major, _ = Major.objects.get_or_create(

            code=code, defaults={'name': name, 'description': description}

        )

        return major


    def make_curriculum(self, major, name, year, entries, credits_to_graduate=None):


        curriculum, _ = Curriculum.objects.get_or_create(

            major=major, year=year,

            defaults={'name': name, 'credits_to_graduate': credits_to_graduate},

        )

        for course, year_level, term, required in entries:

            CurriculumCourse.objects.get_or_create(

                curriculum=curriculum,

                course=course,

                defaults={'year_level': year_level, 'term': term, 'is_required': required},

            )

        return curriculum


    def make_file_material(self, course, title):

        if course.materials.filter(title=title).exists():

            return

        material = Material(course=course, title=title, type=Material.PDF)

        material.file_url.save(

            f'{title.lower().replace(" ", "_")}.pdf', ContentFile(SAMPLE_PDF), save=False

        )

        material.save()


    def make_link_material(self, course, title, url):

        Material.objects.get_or_create(

            course=course, title=title,

            defaults={'type': Material.LINK, 'link_url': url},

        )


    def make_announcement(self, course, author, title, content):

        Announcement.objects.get_or_create(

            course=course, title=title,

            defaults={'author': author, 'content': content},

        )


    def enroll(self, student, course, status=Enrollment.ACTIVE):

        Enrollment.objects.get_or_create(

            student=student, course=course, defaults={'status': status}

        )


    def make_assignment(self, course, title, description, type_, due, max_score):

        assignment, _ = Assignment.objects.get_or_create(

            course=course, title=title,

            defaults={

                'description': description,

                'type': type_,

                'due_date': due,

                'max_score': max_score,

            },

        )

        return assignment


    def make_question(self, quiz, text, points, order, choices, qtype=QuizQuestion.SINGLE):

        question, created = QuizQuestion.objects.get_or_create(

            assignment=quiz, text=text,

            defaults={'points': points, 'order': order, 'type': qtype},

        )

        if created:

            for index, (choice_text, is_correct) in enumerate(choices):

                QuizChoice.objects.create(

                    question=question, text=choice_text,

                    is_correct=is_correct, order=index,

                )

        return question


    def make_submission(self, assignment, student, grade=None, feedback=''):

        if Submission.objects.filter(assignment=assignment, student=student).exists():

            return

        submission = Submission(

            assignment=assignment, student=student, grade=grade, feedback=feedback

        )

        submission.file_url.save(

            f'{student.username}_{assignment.id}.pdf', ContentFile(SAMPLE_PDF), save=False

        )

        submission.save()


    def take_quiz(self, quiz, student, correct_ratio=1.0):


        if QuizAttempt.objects.filter(assignment=quiz, student=student).exists():

            return

        if Submission.objects.filter(assignment=quiz, student=student).exists():

            return


        attempt = QuizAttempt.objects.create(assignment=quiz, student=student)

        questions = list(quiz.questions.all())

        answer_correctly_up_to = int(len(questions) * correct_ratio)

        score = 0


        for index, question in enumerate(questions):

            want_correct = index < answer_correctly_up_to

            choice = question.choices.filter(is_correct=want_correct).first()

            if not choice:

                choice = question.choices.first()

            if not choice:

                continue

            if choice.is_correct:

                score += question.points

            QuizAnswer.objects.create(

                attempt=attempt, question=question,

                selected_choice=choice, is_correct=choice.is_correct,

            )


        attempt.score = min(score, quiz.max_score)

        attempt.save(update_fields=['score'])

        Submission.objects.create(

            assignment=quiz, student=student,

            grade=attempt.score, feedback='Auto-graded quiz submission.',

        )


    def recompute_progress(self):

        from assignments.views import update_enrollment_progress


        for enrollment in Enrollment.objects.select_related('student', 'course'):

            update_enrollment_progress(enrollment.student, enrollment.course)


    def report(self, admin, smith, chen, students, pending):

        line = '=' * 62

        out = self.stdout

        out.write('')

        out.write(self.style.SUCCESS(line))

        out.write(self.style.SUCCESS('  Demo data ready'))

        out.write(self.style.SUCCESS(line))

        out.write(f'  Password for every account below: {PASSWORD}')

        out.write('')

        out.write('  ADMIN')

        out.write(f'    {admin.username:<14} also a Django superuser (/admin/)')

        out.write('  INSTRUCTORS')

        out.write(f'    {smith.username:<14} Intro to Programming, Web Dev, COBOL (archived)')

        out.write(f'    {chen.username:<14} Statistics, Machine Learning (draft)')

        out.write('  STUDENTS')

        for student in students:

            courses = ', '.join(

                e.course.title for e in student.enrollments.select_related('course')

            ) or 'not enrolled'

            out.write(f'    {student.username:<14} {courses}')

        out.write('')

        out.write('  Things worth trying:')

        out.write(f'    - Log in as admin and approve "{pending.title}" (currently draft)')

        out.write('    - Log in as prof.smith to grade carla\'s ungraded FizzBuzz submission')

        out.write('    - Log in as carla and take "Quiz 1 - Python Basics" (not yet attempted)')

        out.write('    - Log in as alice to see grades, feedback and progress')

        out.write(self.style.SUCCESS(line))

        out.write('')
