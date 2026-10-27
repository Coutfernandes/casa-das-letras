"""
Configurações do projeto Casa das Letras.

Valores sensíveis ou que mudam entre ambientes (desenvolvimento e produção)
vêm do arquivo backend/.env, lido pelo django-environ. Nada secreto fica
escrito neste arquivo, porque ele vai para o repositório público.
"""

from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# Caminhos e variáveis de ambiente
# ---------------------------------------------------------------------------

# Pasta backend/ (settings.py -> core/ -> backend/).
BASE_DIR = Path(__file__).resolve().parent.parent

# DJANGO_DEBUG é lido como booleano e, se faltar, vale False (o lado seguro).
env = environ.Env(DJANGO_DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Segurança
# ---------------------------------------------------------------------------

# Sem valor padrão de propósito: sem a chave, o Django não inicia.
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env("DJANGO_DEBUG")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Sites que podem enviar POST com o cookie de sessão (proteção CSRF).
# Desenvolvimento: o Vite em localhost:5173. Produção: o domínio da Vercel.
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Chave do HMAC que gera os pseudônimos públicos (apps/accounts/aliases.py).
ALIAS_SECRET = env("ALIAS_SECRET")

# Chave privada Ed25519 que assina a âncora de cada lote (apps/audit/signing.py).
# Base64 dos 32 bytes da chave; gere com "python manage.py generate_signing_key".
# Vazia, o Django inicia, mas todo lance é recusado até a chave ser configurada.
AUDIT_SIGNING_KEY = env("AUDIT_SIGNING_KEY", default="")

# Redis que guarda a cópia externa das âncoras (apps/audit/anchors.py).
# Vazio, a cópia fica desligada (desenvolvimento sem Redis).
REDIS_URL = env("REDIS_URL", default="")

# ---------------------------------------------------------------------------
# Aplicações
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "channels",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.catalog",
    "apps.auctions",
    "apps.bids",
    "apps.wallet",
    "apps.audit",
]

INSTALLED_APPS = ["daphne", *DJANGO_APPS, *THIRD_PARTY_APPS, *LOCAL_APPS]

# ---------------------------------------------------------------------------
# Tempo real (WebSocket)
# ---------------------------------------------------------------------------

ASGI_APPLICATION = "core.asgi.application"

# Em desenvolvimento, as mensagens ficam na memória do próprio servidor.
# Em produção, com mais de um processo, entra o Redis (parte 7).
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

# DATABASE_URL no formato postgres://usuario:senha@endereco:porta/banco.
# Em produção muda só o .env (apontando para o Neon); este código fica igual.
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Cache (resultados da busca na Open Library)
# ---------------------------------------------------------------------------

# Desenvolvimento: memória do próprio processo, sem instalar nada.
# Produção: o Redis da VM, informado em DJANGO_CACHE_URL (redis://...).
CACHES = {
    "default": env.cache("DJANGO_CACHE_URL", default="locmemcache://"),
}

# ---------------------------------------------------------------------------
# Usuários e senhas
# ---------------------------------------------------------------------------

# Usuário personalizado: login por e-mail, papel e pseudônimo (apps/accounts).
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Idioma e fuso horário
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "pt-br"

# Fuso usado só para exibir datas. Com USE_TZ = True, tudo é gravado em UTC,
# o que mantém o hash dos lances igual em qualquer fuso (seção 7 da spec).
TIME_ZONE = "America/Manaus"

USE_I18N = True

USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estáticos (CSS e JS do painel de administração)
# ---------------------------------------------------------------------------

STATIC_URL = "static/"

# Pasta onde o collectstatic junta os arquivos no deploy (ignorada pelo Git).
STATIC_ROOT = BASE_DIR / "staticfiles"


# Arquivos gravados pelo sistema: as capas baixadas da Open Library.
# Em produção, o Nginx serve esta pasta, no disco da VM da Oracle.
MEDIA_URL = "media/"
MEDIA_ROOT = env.path("DJANGO_MEDIA_ROOT", default=BASE_DIR / "media")



# ---------------------------------------------------------------------------
# API (Django REST Framework)
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    # Login por sessão: cookie HttpOnly, com proteção contra CSRF.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Fechado por padrão: toda rota exige login, a não ser que declare
    # permission_classes = [AllowAny] (vitrine, auditoria, comprovante).
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
        # Erros de regra de negócio viram 422 com code, message e data.
    "EXCEPTION_HANDLER": "core.exception_handler.api_exception_handler",
}
