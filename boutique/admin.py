from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Look, Store, SiteSettings

admin.site.site_header = "Colibri LOOK · управление сайтом"
admin.site.site_title = "Colibri LOOK"
admin.site.index_title = "Контент бутика"

class BrandedAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("css/admin.css",)}

    @admin.display(description="Фото")
    def preview(self, obj):
        return format_html('<img src="{}" alt="" width="45" height="60" style="object-fit:cover">', obj.image_url) if obj.image_url else "—"

@admin.register(Category)
class CategoryAdmin(BrandedAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    fields = ("image", "image_alt", "order")
    extra = 1

@admin.register(Product)
class ProductAdmin(BrandedAdmin):
    list_display = ("preview", "name", "category", "price", "availability", "is_published", "is_featured")
    list_display_links = ("preview", "name")
    list_filter = ("is_published", "category", "availability", "is_featured")
    search_fields = ("name", "description", "colors")
    list_editable = ("price", "availability", "is_published", "is_featured")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25
    save_on_top = True
    inlines = [ProductImageInline]
    readonly_fields = ("preview", "updated_at")
    fieldsets = (
        ("Товар", {"fields": ("name", "slug", "category", "description")}),
        ("Фото", {"fields": ("preview", "image", "image_alt", "card_focus", "video"), "description": "JPEG, PNG или WebP до 8 МБ. Дополнительные фото — в галерее внизу."}),
        ("Цена и параметры", {"fields": ("price", "price_checked_at", "sizes", "colors", "composition", "availability")}),
        ("Публикация", {"fields": ("is_published", "is_featured", "order")}),
        ("Источник", {"fields": ("source_url", "updated_at"), "classes": ("collapse",)}),
    )

@admin.register(Look)
class LookAdmin(BrandedAdmin):
    list_display = ("preview", "title", "is_published", "order")
    list_display_links = ("preview", "title")
    list_editable = ("is_published", "order")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("products",)
    search_fields = ("title",)
    fields = ("title", "slug", "description", "image", "image_alt", "video", "on_home", "hero_image", "hero_detail", "products", "is_published", "order", "source_url")

@admin.register(Store)
class StoreAdmin(BrandedAdmin):
    list_display = ("name", "address", "phone", "is_active")

@admin.register(SiteSettings)
class SiteSettingsAdmin(BrandedAdmin):
    fields = ("tagline", "intro", "image", "image_alt", "video", "about_title", "about_text", "telegram_url", "instagram_url", "seo_description")

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False
