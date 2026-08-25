from rest_framework.exceptions import PermissionDenied, ValidationError


def resolve_student_id(request, param='student'):


    raw = request.query_params.get(param)

    if not raw:

        return request.user.id


    try:

        student_id = int(raw)

    except (TypeError, ValueError):

        raise ValidationError({param: 'Must be a numeric user id.'})


    if request.user.is_admin or request.user.is_instructor:

        return student_id

    if student_id != request.user.id:

        raise PermissionDenied('You can only view your own record.')

    return student_id
