"""Cópia local dos livros da Open Library."""

from django.db import models

from core.models import UUIDModel


class CatalogItemSnapshot(UUIDModel):
    """
    Dados do livro copiados da Open Library ao criar o lote.

    Vitrine, sala, auditoria e comprovante leem sempre daqui, nunca da API.
    Assim, tudo continua funcionando mesmo com a Open Library fora do ar.
    """

    ol_work_key = models.CharField("chave da obra na Open Library", max_length=50, db_index=True)
    title = models.CharField("título", max_length=300)
    authors = models.JSONField("autores", default=list, blank=True)
    first_publish_year = models.PositiveSmallIntegerField(
        "ano da primeira publicação", null=True, blank=True
    )
    edition_count = models.PositiveIntegerField("número de edições", null=True, blank=True)

    cover = models.FileField("capa", upload_to="covers/", blank=True)
    cover_source_url = models.URLField("endereço da capa na Open Library", blank=True)

    raw = models.JSONField("resposta original da API", default=dict, blank=True)
    created_at = models.DateTimeField("copiado em", auto_now_add=True)

    class Meta:
        verbose_name = "livro"
        verbose_name_plural = "livros"

    def __str__(self):
        return self.title

    @property
    def cover_url(self):
        """Capa salva no nosso servidor e, se não houver, a da Open Library."""
        if self.cover:
            return self.cover.url
        return self.cover_source_url
