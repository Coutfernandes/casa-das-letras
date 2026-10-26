"""Criação de usuários com e-mail como login."""

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        if not extra_fields.get("role"):
            raise ValueError("O papel (leiloeiro ou licitante) é obrigatório.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # O superusuário administra o sistema pelo painel /admin.
        # Ele precisa de um papel, e leiloeiro é o que não dá lances.
        extra_fields.setdefault("role", self.model.Role.AUCTIONEER)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superusuário precisa de is_staff=True e is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
