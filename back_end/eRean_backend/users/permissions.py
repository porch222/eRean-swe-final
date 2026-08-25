from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class IsAdmin(IsAuthenticated):

    def has_permission(self, request, view):

        return super().has_permission(request, view) and request.user.is_admin


class IsInstructor(IsAuthenticated):

    def has_permission(self, request, view):

        return super().has_permission(request, view) and request.user.is_instructor


class IsStudent(IsAuthenticated):

    def has_permission(self, request, view):

        return super().has_permission(request, view) and request.user.is_student


class IsAdminOrInstructor(IsAuthenticated):

    def has_permission(self, request, view):

        return super().has_permission(request, view) and (

            request.user.is_admin or request.user.is_instructor

        )


class IsAdminOrInstructorOrReadOnly(IsAuthenticated):


    def has_permission(self, request, view):

        if not super().has_permission(request, view):

            return False

        if request.method in SAFE_METHODS:

            return True

        return request.user.is_admin or request.user.is_instructor
