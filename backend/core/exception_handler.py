"""Transforma erros de regra de negócio em respostas da API."""

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .exceptions import BusinessRuleError


def api_exception_handler(exc, context):
    if isinstance(exc, BusinessRuleError):
        return Response(
            {"code": exc.code, "message": exc.message, "data": exc.data},
            status=exc.status_code,
        )
    return drf_exception_handler(exc, context)