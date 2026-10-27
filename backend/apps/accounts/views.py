"""Rotas de autenticação: CSRF, cadastro, login, logout e usuário atual."""

from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .tickets import TICKET_SECONDS, issue_ticket
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """Entrega o cookie csrftoken. O front chama ao abrir, antes de qualquer POST."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    """Cria a conta e já deixa a pessoa logada."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    """Confere e-mail e senha e abre a sessão."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        login(request, serializer.validated_data["user"])
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    """Encerra a sessão: o cookie deixa de valer na hora."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """Quem está logado. O front usa ao abrir para saber se há sessão."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

class WsTicketView(APIView):
    """Um ticket de 30 segundos para identificar o usuário na conexão WebSocket."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"ticket": issue_ticket(request.user), "expires_in": TICKET_SECONDS})
