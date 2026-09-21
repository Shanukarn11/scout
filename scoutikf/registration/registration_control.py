from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render

from .models import RegistrationControl


def registration_state(level):
    control = RegistrationControl.current()
    if level == 1:
        return control.level1_open, control.level1_message, control.common_message
    if level == 2:
        return control.level2_open, control.level2_message, control.common_message
    if level == "scoutlens":
        return control.scoutlens_open, control.scoutlens_message, control.common_message
    raise ValueError(f"Unknown registration level: {level}")


def require_registration_open(level, *, page=False, template_name="registration_closed.html", display_name=None):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            is_open, level_message, common_message = registration_state(level)
            if is_open:
                return view(request, *args, **kwargs)
            if page:
                response = render(
                    request,
                    template_name,
                    {
                        "level": level,
                        "registration_name": display_name or f"Level {level}",
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
