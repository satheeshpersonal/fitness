# utils/exception_handler.py

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status as drf_status

def custom_exception_handler(exc, context):
    # Call DRF's default exception handler first to get the standard error response
    response = exception_handler(exc, context)

    if response is not None:
        # Extract the default error details
        message = ""
        code = "error"

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = response.data['detail']
            else:
                # Combine all error messages (e.g., from serializer validation)
                messages = []
                for field, errors in response.data.items():
                    messages.append(f"{field}: {', '.join(errors)}")
                message = " | ".join(messages)

        return Response({
            "status": "failure",
            "data": {},
            "error": {
                "code": code,
                "message": str(message)
            }
        }, status=response.status_code)

    # Fallback: if DRF didn't handle it
    return Response({
        "status": "failure",
        "data": {},
        "error": {
            "code": "server_error",
            "message": "Something went wrong. Please try again."
        }
    }, status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR)
