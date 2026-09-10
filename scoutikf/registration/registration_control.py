from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render

from .models import RegistrationControl


def registration_is_open(level):
    control = RegistrationControl.current()
    return (control.level1_open if level == 1 else control.level2_open), control.closed_message


def require_registration_open(level, *, page=False):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            is_open, message = registration_is_open(level)
            if is_open:
                return view(request, *args, **kwargs)
            if page:
                response = render(
                    request,
                    "registration_closed.html",
                    {"level": level, "closed_message": message},
                )
                response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                return response
            return JsonResponse(
                {"error": True, "message": message, "registration_level": level},
                status=403,
            )
        return wrapped
    return decorator
