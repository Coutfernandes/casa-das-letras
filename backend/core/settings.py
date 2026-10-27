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

# O Render cria esta variável sozinho com o endereço do serviço (casa-das-letras.onrender.com).
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Sites que podem enviar POST com o cookie de sessão (proteção CSRF).
# Desenvolvimento: o Vite em localhost:5173. Produção: o domínio da Vercel.
# A mesma lista libera a origem do WebSocket (core/asgi.py).
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Cookie de sessão fora do alcance do JavaScript e só em navegação do próprio site.
# O csrftoken fica legível (padrão do Django): o frontend o copia no header X-CSRFToken.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if not DEBUG:
    # O Render recebe o HTTPS e repassa ao Daphne em HTTP, avisando no header X-Forwarded-Proto.
    # Com isto, o Django sabe que o pedido original era seguro.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Os cookies só viajam por HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Segredo que o cron-job.org manda em POST /api/internal/tick/. Vazio, a rota fica desligada (404).
CRON_SECRET = env("CRON_SECRET", default="")

# Baixar a capa ao criar um lote. No Render não há disco permanente: lá fica False,
# e o lote usa só o endereço da capa na Open Library.
COVER_DOWNLOAD = env.bool("COVER_DOWNLOAD", default=True)

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
    "apps.seed",
]

INSTALLED_APPS = ["daphne", *DJANGO_APPS, *THIRD_PARTY_APPS, *LOCAL_APPS]

# ---------------------------------------------------------------------------
# Tempo real (WebSocket)
# ---------------------------------------------------------------------------

ASGI_APPLICATION = "core.asgi.application"

# As mensagens da sala ficam na memória do próprio servidor, no local e no Render.
# Só funciona com UM processo do Daphne: um segundo processo não veria os lances do primeiro.
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serve os arquivos estáticos (CSS e JS do admin) direto do Django, sem Nginx.
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
# Em produção muda só a variável (o Neon, com ?sslmode=require no fim); este código fica igual.
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Quantos segundos uma conexão com o banco é reaproveitada. O padrão 0 abre uma por pedido:
# a documentação do Django recomenda desligar as conexões persistentes sob ASGI (Daphne),
# porque cada pedido pode rodar numa thread diferente e as conexões abertas se acumulam.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DJANGO_CONN_MAX_AGE", default=0)
# Antes de reaproveitar uma conexão, confere se ela ainda está viva (o Neon fecha as ociosas).
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Cache (resultados da busca na Open Library)
# ---------------------------------------------------------------------------

# Memória do próprio processo, sem instalar nada. Com um processo só no Render, basta.
# Para usar um Redis como cache, informe DJANGO_CACHE_URL (redis://...).
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
# Só no desenvolvimento: no Render, COVER_DOWNLOAD é False e nada é gravado aqui.
MEDIA_URL = "media/"
MEDIA_ROOT = env.path("DJANGO_MEDIA_ROOT", default=BASE_DIR / "media")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Em produção, o WhiteNoise guarda cada arquivo comprimido e com o hash no nome
    # (base.3f9a1c.css), para o navegador guardar em cache sem medo de versão velha.
    # Esse modo exige o collectstatic antes; no desenvolvimento (e nos testes), fica o simples.
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

# Tudo vai para o console: o Render mostra o console na aba Logs.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


# ---------------------------------------------------------------------------
# API (Django REST Framework)
# ---------------------------------------------------------------------------

# Lida como texto: uma variável criada vazia no painel do Render vale como "não configurada".
DRF_NUM_PROXIES = env("DRF_NUM_PROXIES", default="")

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
    # Limites de acesso por escopo. Só valem nas rotas que declaram throttle_scope.
    # Acima do limite, o DRF responde 429 (Too Many Requests).
    "DEFAULT_THROTTLE_RATES": {
        "audit": "30/min",
    },
    # Quantos proxies ficam entre o navegador e o Django, para o limite acima contar o IP de
    # quem acessa, e não o do proxy. Em produção o pedido passa pela Vercel (o rewrite de /api)
    # e pelo proxy do Render; o valor certo será conferido no header X-Forwarded-For depois
    # do deploy. Vazio (None, no local), o DRF usa o X-Forwarded-For inteiro ou o REMOTE_ADDR.
    "NUM_PROXIES": int(DRF_NUM_PROXIES) if DRF_NUM_PROXIES else None,
}
