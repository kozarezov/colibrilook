from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from boutique import views
from config.health import health

urlpatterns = [
    path("healthz/", health, name="health"),
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("catalog/<slug:slug>/", views.product_detail, name="product"),
    path("looks/", views.looks, name="looks"),
    path("looks/<slug:slug>/", views.look_detail, name="look"),
    path("about/", views.about, name="about"),
    path("contacts/", views.contacts, name="contacts"),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler404 = "boutique.views.not_found"
