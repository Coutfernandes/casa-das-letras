"""
Busca de livros na Open Library, com cache e tolerância a falhas.

É a única parte do sistema que fala com a API externa. Vitrine, sala,
auditoria e comprovante leem a cópia local (CatalogItemSnapshot) e
continuam funcionando com a Open Library fora do ar.
"""
import hashlib
import logging
import time
from dataclasses import asdict, dataclass

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
# Só os campos usados: pedir todos (fields=*) gera uma resposta pesada.
SEARCH_FIELDS = "key,title,author_name,first_publish_year,cover_i,edition_count"
USER_AGENT = "CasaDasLetras/1.0 (+https://github.com/Coutfernandes/casa-das-letras)"

PAGE_SIZE = 20
TIMEOUT_SECONDS = 5
MAX_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 1

MAX_COVER_BYTES = 5 * 1024 * 1024  # 5 MB: capas maiores são ignoradas
CACHE_SECONDS = 10 * 60  # resultado "fresco": 10 minutos
BACKUP_CACHE_SECONDS = 7 * 24 * 60 * 60  # cópia de reserva para a API fora do ar: 7 dias


class CatalogUnavailable(Exception):
    """A Open Library não respondeu e não há resultado guardado para a busca."""


@dataclass(frozen=True)
class CatalogBook:
    """Um livro da busca, já limpo e no formato que o sistema usa."""

    work_key: str
    title: str
    authors: list[str]
    first_publish_year: int | None
    edition_count: int | None
    cover_id: int

    @property
    def cover_url(self) -> str:
        return COVER_URL.format(cover_id=self.cover_id)


@dataclass(frozen=True)
class SearchResult:
    books: list[CatalogBook]
    # Verdadeiro quando a API falhou e os livros vieram da cópia de reserva.
    is_stale: bool


def search_books(query: str, page: int = 1) -> SearchResult:
    """Busca livros por título ou autor. Lança CatalogUnavailable se não houver o que mostrar."""
    query = " ".join(query.split())
    # Hash da busca na chave: tamanho fixo e sem espaços nem símbolos digitados.
    query_hash = hashlib.sha256(query.lower().encode()).hexdigest()
    cache_key = f"catalog:search:{query_hash}:{page}"
    backup_key = f"{cache_key}:backup"

    cached = cache.get(cache_key)
    if cached is not None:
        return SearchResult(books=_books_from_cache(cached), is_stale=False)

    try:
        books = _fetch_books(query, page)
    except requests.RequestException as error:
        logger.warning("Open Library indisponível na busca %r: %s", query, error)
        backup = cache.get(backup_key)
        if backup is None:
            raise CatalogUnavailable from error
        return SearchResult(books=_books_from_cache(backup), is_stale=True)

    payload = [asdict(book) for book in books]
    cache.set(cache_key, payload, CACHE_SECONDS)
    cache.set(backup_key, payload, BACKUP_CACHE_SECONDS)
    return SearchResult(books=books, is_stale=False)

def fetch_cover(book: CatalogBook) -> bytes | None:
    """Baixa a capa do livro. Devolve None se falhar: o lote usa o endereço da Open Library."""
    try:
        response = requests.get(
            book.cover_url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
    except requests.RequestException as error:
        logger.warning("Não foi possível baixar a capa %s: %s", book.cover_url, error)
        return None

    is_image = response.headers.get("Content-Type", "").startswith("image/")
    if not is_image or len(response.content) > MAX_COVER_BYTES:
        logger.warning("Capa recusada (tipo ou tamanho inválido): %s", book.cover_url)
        return None
    return response.content

def _fetch_books(query: str, page: int) -> list[CatalogBook]:
    params = {"q": query, "page": page, "limit": PAGE_SIZE, "fields": SEARCH_FIELDS}
    data = _get_json(SEARCH_URL, params)
    books = (_parse_book(doc) for doc in data.get("docs", []))
    return [book for book in books if book is not None]


def _get_json(url: str, params: dict) -> dict:
    """GET com uma nova tentativa em falhas passageiras (tempo esgotado, erro 5xx)."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                url, params=params, timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            if attempt == MAX_ATTEMPTS or not _is_temporary(error):
                raise
            time.sleep(RETRY_DELAY_SECONDS)
    raise AssertionError("inalcançável")


def _is_temporary(error: requests.RequestException) -> bool:
    if isinstance(error, (requests.Timeout, requests.ConnectionError)):
        return True
    response = getattr(error, "response", None)
    return response is not None and response.status_code >= 500


def _parse_book(doc: dict) -> CatalogBook | None:
    """Converte um resultado da API. Descarta os sem capa, título ou chave."""
    work_key, title, cover_id = doc.get("key"), doc.get("title"), doc.get("cover_i")
    if not isinstance(work_key, str) or not isinstance(title, str) or not isinstance(cover_id, int):
        return None

    authors = doc.get("author_name") or []
    year = doc.get("first_publish_year")
    editions = doc.get("edition_count")
    return CatalogBook(
        work_key=work_key,
        title=title,
        authors=[name for name in authors if isinstance(name, str)],
        first_publish_year=year if isinstance(year, int) else None,
        edition_count=editions if isinstance(editions, int) else None,
        cover_id=cover_id,
    )


def _books_from_cache(payload: list[dict]) -> list[CatalogBook]:
    return [CatalogBook(**item) for item in payload]