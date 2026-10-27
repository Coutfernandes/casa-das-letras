"""Endereços de autenticação, montados em /api/auth/ pelo core/urls.py."""

from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.CsrfView.as_view(), name="auth-csrf"),
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path("ws-ticket/", views.WsTicketView.as_view(), name="auth-ws-ticket"),
]
