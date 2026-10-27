"""Rotas do próprio projeto, que não pertencem a nenhum app."""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    """O Render chama esta rota para saber se o servidor está de pé. Não toca no banco."""
    return Response({"status": "ok"})
