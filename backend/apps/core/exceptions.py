from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class BusinessError(APIException):
    """Ошибка бизнес-правила: машинный код + человекочитаемое описание (+ детали для формы)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "business_error"

    def __init__(self, code, message, *, errors=None, status_code=None):
        super().__init__(detail=message, code=code)
        self.error_code = code
        self.errors = errors or []
        if status_code:
            self.status_code = status_code


class ConflictError(BusinessError):
    status_code = status.HTTP_409_CONFLICT


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and isinstance(exc, BusinessError):
        response.data = {"code": exc.error_code, "detail": str(exc.detail), "errors": exc.errors}
    return response
