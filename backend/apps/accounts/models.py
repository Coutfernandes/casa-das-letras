"""Usuário do sistema, com e-mail como login e papel de leiloeiro ou licitante."""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .aliases import build_public_alias
from .managers import UserManager

# Tamanhos tentados para o pseudônimo, do mais curto ao mais longo.
# Uma colisão com 6 caracteres é rara; com 12, praticamente impossível.
ALIAS_LENGTHS = (6, 8, 12)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        AUCTIONEER = "AUCTIONEER", "Leiloeiro"
        BIDDER = "BIDDER", "Licitante"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("e-mail", unique=True)
    name = models.CharField("nome", max_length=150)
    role = models.CharField("papel", max_length=10, choices=Role.choices)
    public_alias = models.CharField(
        "pseudônimo público", max_length=40, unique=True, editable=False
    )
    is_active = models.BooleanField("ativo", default=True)
    is_staff = models.BooleanField("acesso ao painel admin", default=False)
    date_joined = models.DateTimeField("cadastrado em", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["AUCTIONEER", "BIDDER"]),
                name="user_role_valid",
            ),
        ]

    def __str__(self):
        return self.email

    @property
    def is_auctioneer(self):
        return self.role == self.Role.AUCTIONEER

    @property
    def is_bidder(self):
        return self.role == self.Role.BIDDER

    def save(self, *args, **kwargs):
        if not self.public_alias:
            self.public_alias = self._unique_public_alias()
        super().save(*args, **kwargs)

    def _unique_public_alias(self):
        others = User.objects.exclude(pk=self.pk)
        for length in ALIAS_LENGTHS:
            alias = build_public_alias(self.id, length)
            if not others.filter(public_alias=alias).exists():
                return alias
        raise RuntimeError("Não foi possível gerar um pseudônimo único.")
