from django.contrib import admin


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


class CurriculumCourseInline(admin.TabularInline):


    model = CurriculumCourse

    extra = 1

    autocomplete_fields = ['course']


@admin.register(Term)

class TermAdmin(admin.ModelAdmin):

    list_display = ('code', 'name', 'year', 'starts_on', 'ends_on', 'is_current')

    list_filter = ('year', 'is_current')

    search_fields = ('code', 'name')


@admin.register(Major)

class MajorAdmin(admin.ModelAdmin):

    list_display = ('code', 'name', 'course_count')

    search_fields = ('code', 'name')


    @admin.display(description='Courses')

    def course_count(self, obj):

        return obj.courses.count()


@admin.register(Curriculum)

class CurriculumAdmin(admin.ModelAdmin):

    list_display = ('name', 'major', 'year', 'is_active', 'total_credits')

    list_filter = ('major', 'is_active', 'year')

    search_fields = ('name', 'major__name', 'major__code')

    inlines = [CurriculumCourseInline]


@admin.register(Course)

class CourseAdmin(admin.ModelAdmin):

    list_display = ('title', 'major', 'term', 'credits', 'instructor', 'status')

    list_filter = ('major', 'term', 'status')

    search_fields = ('title', 'description')


admin.site.register(Material)

admin.site.register(Announcement)

admin.site.register(AnnouncementRead)

admin.site.register(ActivityLog)
