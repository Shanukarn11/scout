from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render

from .models import RegistrationControl


def registration_state(level):
    control = RegistrationControl.current()
    if level == 1:
        return control.level1_open, control.level1_message, control.common_message
    return control.level2_open, control.level2_message, control.common_message


def require_registration_open(level, *, page=False):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            is_open, level_message, common_message = registration_state(level)
            if is_open:
                return view(request, *args, **kwargs)
            if page:
                response = render(
                    request,
                    "registration_closed.html",
                    {
                        "level": level,
                        "level_message": level_message,
                        "common_message": common_message,
                    },
                )
                response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                return response
            message = " ".join(part for part in (level_message, common_message) if part)
            return JsonResponse(
                {"error": True, "message": message, "registration_level": level},
                status=403,
            )
        return wrapped
    return decorator
