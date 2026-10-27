"""Mapa de endereços do projeto."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/catalog/", include("apps.catalog.urls")),
    path("api/wallet/", include("apps.wallet.urls")),
    path("api/", include("apps.auctions.urls")),
    path("api/", include("apps.bids.urls")),
    path("api/", include("apps.audit.urls")),
]

# No desenvolvimento, o próprio Django serve as capas.
# Em produção, quem faz isso é o Nginx, e esta linha não tem efeito.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
