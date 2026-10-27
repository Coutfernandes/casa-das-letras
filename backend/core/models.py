"""Peças reutilizadas pelos modelos de todos os apps."""

import uuid

from django.db import models


class UUIDModel(models.Model):
    """Base com id UUID: não revela quantos registros existem nem a ordem deles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True



class AppendOnlyModel(models.Model):
    """
    Registro que o código só pode criar, nunca alterar nem apagar.

    Usado em lances, carteira e comprovantes. Uma alteração feita direto no
    banco, por fora do código, é detectada pela auditoria (seção 7 da spec).
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError(f"{self._meta.verbose_name} não pode ser alterado depois de criado.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError(f"{self._meta.verbose_name} não pode ser apagado.")
