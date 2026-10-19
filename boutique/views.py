import re
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from .models import Category, Product, Look, SiteSettings, Store

def published_products():
    return Product.objects.filter(is_published=True, category__is_active=True).select_related("category")

@require_GET
def home(request):
    site = SiteSettings.load()
    looks = Look.objects.filter(is_published=True)
    products = published_products()
    groups = [
        {"key": "all", "title": "Выбор Colibri", "products": products.filter(is_featured=True)[:4]},
        {"key": "outerwear", "title": "Верхняя одежда", "products": products.filter(category__slug="outerwear")[:4]},
        {"key": "suits", "title": "Костюмы", "products": products.filter(category__slug="suits")[:4]},
        {"key": "tops", "title": "Топы и рубашки", "products": products.filter(category__slug="tops")[:4]},
    ]
    selected = request.GET.get("collection", "all")
    if selected not in {g["key"] for g in groups}:
        selected = "all"
    categories = []
    for slug in ["outerwear", "suits", "tops", "accessories"]:
        category_products = products.filter(category__slug=slug)
        product = category_products.filter(is_featured=False).exclude(slug="peplum").first() or category_products.first()
        if product:
            categories.append({"category": product.category, "product": product})
    return render(request, "boutique/home.html", {
        "featured": groups[0]["products"], "product_groups": groups,
        "selected_collection": selected, "category_cards": categories,
        "looks": looks[:6], "hero_scenes": looks.filter(on_home=True)[:5],
        "details_selection": products.filter(category__slug__in=["accessories", "fragrance"]).exclude(slug="peplum")[:3],
        "fittings": looks.filter(~Q(seed_video="") | ~Q(video=""))[:3],
    })

@require_GET
def catalog(request):
    products = published_products()
    category = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()[:120]
    if request.GET.get("clear") == "1":
        query = ""
    size = request.GET.get("size", "")[:20]
    sort = request.GET.get("sort", "new")
    if category:
        products = products.filter(category__slug=category)
    if query:
        # SQLite LIKE does not fold Cyrillic case. Escaped iregex is Unicode-aware.
        pattern = re.escape(query)
        products = products.filter(Q(name__iregex=pattern) | Q(description__iregex=pattern) | Q(colors__iregex=pattern))
    if size:
        # Match complete size tokens, not S within XS.
        ids = [p.pk for p in products.only("pk", "sizes", "category_id") if size in p.size_options]
        products = products.filter(pk__in=ids)
    ordering = {"new": ("order", "-created_at"), "price": (F("price").asc(nulls_last=True), "pk"),
                "price-desc": (F("price").desc(nulls_last=True), "pk")}
    products = products.order_by(*ordering.get(sort, ordering["new"]))
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    if request.GET.get("clear") == "1":
        params.pop("clear", None)
        params.pop("q", None)
    clear_params = params.copy()
    clear_params.pop("q", None)
    categories = Category.objects.filter(is_active=True)
    size_options = sorted({s for p in published_products().only("sizes", "category_id") for s in p.size_options})
    return render(request, "boutique/catalog.html", {"page_obj": page, "categories": categories,
        "selected_category": category, "query": query, "selected_size": size, "sort": sort,
        "size_options": size_options, "filter_query": params.urlencode(), "clear_query": clear_params.urlencode()})

@require_GET
def product_detail(request, slug):
    product = get_object_or_404(published_products(), slug=slug)
    size = request.GET.get("size", "")
    if size not in product.size_options:
        size = ""
    contacts = [{"store": store, "url": store.inquiry_url(product, size)} for store in Store.objects.filter(is_active=True)]
    return render(request, "boutique/product.html", {"product": product, "selected_size": size,
        "contacts": contacts, "related": published_products().filter(category=product.category).exclude(pk=product.pk)[:4]})

@require_GET
def looks(request):
    return render(request, "boutique/looks.html", {"looks": Look.objects.filter(is_published=True)})

@require_GET
def look_detail(request, slug):
    look = get_object_or_404(Look.objects.filter(is_published=True), slug=slug)
    return render(request, "boutique/look.html", {"look": look,
        "products": published_products().filter(looks=look)})

@require_GET
def about(request):
    return render(request, "boutique/about.html")

@require_GET
def contacts(request):
    return render(request, "boutique/contacts.html")

def not_found(request, exception):
    return render(request, "404.html", status=404)
