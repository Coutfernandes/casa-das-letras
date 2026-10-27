"""Livros da Open Library na API: resultado da busca e livro escolhido para o lote."""

from rest_framework import serializers


class CatalogBookSerializer(serializers.Serializer):
    """
    Um livro da busca. Serve nos dois sentidos: a busca devolve neste formato,
    e o painel manda o livro escolhido de volta, neste mesmo formato, ao criar o lote.
    """

    work_key = serializers.RegexField(r"^/works/OL\d+W$", max_length=50)
    title = serializers.CharField(max_length=300)
    authors = serializers.ListField(
        child=serializers.CharField(max_length=200), max_length=20, default=list
    )
    first_publish_year = serializers.IntegerField(
        min_value=0, max_value=3000, allow_null=True, default=None
    )
    edition_count = serializers.IntegerField(min_value=0, allow_null=True, default=None)
    cover_id = serializers.IntegerField(min_value=1)
    cover_url = serializers.CharField(read_only=True)


class CatalogSearchQuerySerializer(serializers.Serializer):
    """Parâmetros da busca: ?q=machado&page=1."""

    q = serializers.CharField(min_length=2, max_length=200)
    page = serializers.IntegerField(min_value=1, max_value=50, default=1)
