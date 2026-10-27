"""Mapa de endereços do projeto."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/wallet/", include("apps.wallet.urls")),
    path("api/", include("apps.auctions.urls")),
    path("api/", include("apps.bids.urls")),
    path("api/", include("apps.audit.urls")),
]

# No desenvolvimento, o próprio Django serve as capas.
# Com DEBUG False, esta linha não tem efeito (e no Render as capas nem são baixadas).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
