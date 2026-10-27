"""Busca de livros na Open Library para o painel do leiloeiro."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAuctioneer

from .open_library import CatalogUnavailable, search_books
from .serializers import CatalogBookSerializer, CatalogSearchQuerySerializer

UNAVAILABLE_MESSAGE = (
    "A busca de livros está indisponível agora. Lotes já criados não são afetados."
)


class CatalogSearchView(APIView):
    permission_classes = [IsAuctioneer]

    def get(self, request):
        query = CatalogSearchQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        try:
            result = search_books(query.validated_data["q"], query.validated_data["page"])
        except CatalogUnavailable:
            return Response(
                {"code": "CATALOG_UNAVAILABLE", "message": UNAVAILABLE_MESSAGE},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "results": CatalogBookSerializer(result.books, many=True).data,
                "is_stale": result.is_stale,
            }
        )
