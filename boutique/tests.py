from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import override_settings
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from urllib.parse import urlparse, parse_qs
from PIL import Image
from .models import Category, Product, Look, Store, SiteSettings
from .validators import validate_image

class StorefrontTests(TestCase):
    def test_home_is_available(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Colibri")

    def test_catalog_has_empty_state(self):
        response = self.client.get("/catalog/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ничего не найдено")

    def test_admin_requires_authentication(self):
        response = self.client.get("/admin/")
        self.assertRedirects(response, "/admin/login/?next=/admin/")

class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Одежда", slug="clothes")
        cls.product = Product.objects.create(name="Лонгслив", slug="longsleeve", category=cls.category,
            description="Мягкая вискоза", colors="Чёрный", price=1960, sizes="S, M", is_published=True)
        cls.draft = Product.objects.create(name="Черновик", slug="draft", category=cls.category, price=999)
        cls.store = Store.objects.create(name="Бутик", address="Адрес", phone="+7 905 401-09-95", telegram="colibrilook", map_url="https://yandex.ru/maps/")

    def test_drafts_hidden_from_listing_and_direct_url(self):
        self.assertNotContains(self.client.get("/catalog/"), "Черновик")
        self.assertEqual(self.client.get("/catalog/draft/").status_code, 404)

    def test_inactive_category_hides_product(self):
        self.category.is_active = False
        self.category.save()
        self.assertNotContains(self.client.get("/catalog/"), "Лонгслив")
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)

    def test_russian_search_case_insensitive(self):
        response = self.client.get("/catalog/", {"q": "ЛОНГСЛИВ"})
        self.assertContains(response, "Лонгслив")
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_search_clear_keeps_other_filters(self):
        response = self.client.get("/catalog/", {"q": "ЛОНГСЛИВ", "category": "clothes", "size": "S"})
        self.assertNotIn("q=", response.context["clear_query"])
        self.assertIn("category=clothes", response.context["clear_query"])
        self.assertIn("size=S", response.context["clear_query"])

    def test_size_filter_matches_exact_token(self):
        Product.objects.create(name="Маленький", slug="small", category=self.category, sizes="XS", is_published=True)
        response = self.client.get("/catalog/", {"size": "S"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertNotContains(response, "Маленький")

    def test_filters_and_invalid_page_are_safe(self):
        for value in ["oops", "-1", "9999999999"]:
            self.assertEqual(self.client.get("/catalog/", {"page": value, "sort": "bad"}).status_code, 200)
        response = self.client.get("/catalog/", {"category": "missing"})
        self.assertContains(response, "Ничего не найдено")

    def test_price_sort(self):
        Product.objects.create(name="Дешевле", slug="cheaper", category=self.category, price=500, is_published=True)
        Product.objects.create(name="Уточнить", slug="ask", category=self.category, is_published=True)
        response = self.client.get("/catalog/", {"sort": "price"})
        self.assertEqual([p.slug for p in response.context["page_obj"]], ["cheaper", "longsleeve", "ask"])

    def test_telegram_inquiry_has_product_and_valid_size(self):
        response = self.client.get(self.product.get_absolute_url(), {"size": "S"})
        url = response.context["contacts"][0]["url"]
        self.assertEqual(urlparse(url).netloc, "t.me")
        self.assertEqual(urlparse(url).path, "/colibrilook")
        self.assertIn("Размер: S", parse_qs(urlparse(url).query)["text"][0])
        response = self.client.get(self.product.get_absolute_url(), {"size": "FAKE"})
        self.assertNotIn("FAKE", response.context["contacts"][0]["url"])

    def test_hidden_look_and_products(self):
        look = Look.objects.create(title="Образ", slug="look", is_published=True)
        look.products.add(self.product, self.draft)
        self.assertNotContains(self.client.get(look.get_absolute_url()), "Черновик")
        look.is_published = False
        look.save()
        self.assertEqual(self.client.get(look.get_absolute_url()).status_code, 404)

    def test_price_validation(self):
        self.product.price = -100
        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_escaping(self):
        self.product.name = '<script>alert("bad")</script>'
        self.product.save()
        response = self.client.get(self.product.get_absolute_url())
        self.assertNotContains(response, '<script>alert("bad")</script>')
        self.assertContains(response, "&lt;script&gt;")

class ContentTests(TestCase):
    def test_seed_preserves_edits(self):
        call_command("seed_content", stdout=StringIO())
        product = Product.objects.first()
        product.name = "Правка редактора"
        product.save()
        call_command("seed_content", stdout=StringIO())
        product.refresh_from_db()
        self.assertEqual(product.name, "Правка редактора")
        self.assertEqual(Product.objects.count(), 20)
        self.assertEqual(Store.objects.count(), 2)
        self.assertEqual(Look.objects.count(), 6)

    def test_singleton(self):
        SiteSettings.objects.create(tagline="Первая")
        with self.assertRaises(ValidationError):
            SiteSettings.objects.create(tagline="Вторая")
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.load().tagline, "Первая")

    def test_seeded_public_routes(self):
        call_command("seed_content", stdout=StringIO())
        paths = ["/", "/catalog/", "/looks/", "/about/", "/contacts/"]
        paths += [p.get_absolute_url() for p in Product.objects.all()]
        paths += [look.get_absolute_url() for look in Look.objects.all()]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_images_reject_non_images_and_oversized(self):
        for name, content in [("bad.svg", b"<svg></svg>"), ("bad.jpg", b"not an image"), ("huge.jpg", b"x" * (8 * 1024 * 1024 + 1))]:
            with self.subTest(name=name), self.assertRaises(ValidationError):
                validate_image(SimpleUploadedFile(name, content))

    def test_image_accepts_valid_jpeg(self):
        stream = BytesIO()
        Image.new("RGB", (8, 8)).save(stream, "JPEG")
        validate_image(SimpleUploadedFile("photo.jpg", stream.getvalue(), content_type="image/jpeg"))

class AdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("editor", "editor@example.invalid", "test-password-only")
        self.category = Category.objects.create(name="Одежда", slug="clothes")

    def test_non_staff_cannot_access_content(self):
        user = get_user_model().objects.create_user("visitor", password="test-password-only")
        self.client.force_login(user)
        self.assertEqual(self.client.get("/admin/boutique/product/").status_code, 302)

    def test_staff_without_permissions_cannot_modify(self):
        user = get_user_model().objects.create_user("limited", password="test-password-only", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/admin/boutique/product/add/").status_code, 403)

    def test_create_product_with_image_video_and_publish(self):
        from django.conf import settings
        from pathlib import Path
        self.client.force_login(self.admin)
        stream = BytesIO()
        Image.new("RGB", (16, 16), "black").save(stream, "JPEG")
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post("/admin/boutique/product/add/", {
                "name": "Новая вещь", "slug": "new-item", "category": self.category.pk, "price": "2500",
                "sizes": "S, M", "availability": "ask", "card_focus": "full", "order": 0, "is_published": "on",
                "image": SimpleUploadedFile("photo.jpg", stream.getvalue(), content_type="image/jpeg"),
                "video": SimpleUploadedFile("fitting.mp4", (Path(settings.BASE_DIR) / "static/video/9926.mp4").read_bytes(), content_type="video/mp4"),
                "photos-TOTAL_FORMS": "0", "photos-INITIAL_FORMS": "0", "photos-MIN_NUM_FORMS": "0", "photos-MAX_NUM_FORMS": "1000",
                "_save": "Сохранить",
            })
            self.assertEqual(response.status_code, 302, response.context and response.context.get("adminform"))
            product = Product.objects.get(slug="new-item")
            self.assertTrue(product.image.storage.exists(product.image.name))
            self.assertTrue(product.video.storage.exists(product.video.name))
            self.assertContains(self.client.get(product.get_absolute_url()), "Новая вещь")
            self.assertContains(self.client.get("/admin/boutique/product/"), "Новая вещь")

    def test_delete_requires_confirmation(self):
        self.client.force_login(self.admin)
        product = Product.objects.create(name="Удалить", slug="delete", category=self.category)
        response = self.client.get(f"/admin/boutique/product/{product.pk}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

class VideoTests(TestCase):
    def test_video_validation_rejects_disguised_html_and_oversize(self):
        from boutique.validators import validate_video
        for name, content in [('fake.mp4', b'<html>not video</html>'), ('huge.mp4', b'x' * (40*1024*1024+1)), ('script.html', b'\x00\x00\x00\x18ftypmp42')]:
            with self.subTest(name=name), self.assertRaises(ValidationError):
                validate_video(SimpleUploadedFile(name, content))

    def test_public_video_is_a_player_not_an_image(self):
        category = Category.objects.create(name='Видео', slug='video')
        product = Product.objects.create(name='Примерка', slug='fitting', category=category, is_published=True, seed_video='video/test.mp4', seed_image='images/test.jpg')
        response = self.client.get(product.get_absolute_url())
        self.assertContains(response, '<video')
        self.assertContains(response, 'controls')
        self.assertContains(response, '/static/video/test.mp4')
        product.is_published = False
        product.save()
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 404)

    def test_draft_hero_is_not_exposed(self):
        Look.objects.create(title='Черновая примерка', slug='draft-film', seed_video='video/private.mp4', is_published=False)
        self.assertNotContains(self.client.get('/'), 'video/private.mp4')

class ImportEvidenceTests(TestCase):
    def test_video_poster_is_not_imported_as_a_photo(self):
        from content.tools.collect_telegram import parse_page
        html = '''<div class="tgme_widget_message_wrap"><div data-post="colibri_look/100"><a class="tgme_widget_message_video_player" href="https://t.me/colibri_look/101?single"><i style="background-image:url('poster.jpg')"></i><video src="film.mp4"></video></a><a class="tgme_widget_message_photo_wrap" href="https://t.me/colibri_look/102?single" style="background-image:url('photo.jpg')"></a><div class="tgme_widget_message_text">Костюм 1000 ₽</div></div>'''
        media = parse_page(html)[0]['media']
        self.assertEqual(media[0], {'type':'video','id':101,'url':'film.mp4','poster':'poster.jpg'})
        self.assertEqual(media[1], {'type':'photo','id':102,'url':'photo.jpg'})

    def test_video_upload_is_saved_and_rendered(self):
        from django.core.files import File
        from django.conf import settings
        from pathlib import Path
        from boutique.validators import validate_video
        category = Category.objects.create(name='Одежда',slug='clothes')
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            with (Path(settings.BASE_DIR)/'static/video/9926.mp4').open('rb') as source:
                video = File(source, name='fitting.mp4')
                validate_video(video)
                product = Product.objects.create(name='Видео', slug='video-upload', category=category, video=video, is_published=True)
            self.assertTrue(product.video.storage.exists(product.video.name))
            self.assertContains(self.client.get(product.get_absolute_url()), product.video.url)

class HomeCollectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Костюмы', slug='suits')
        cls.product = Product.objects.create(name='Открытый костюм', slug='public-suit', category=cls.category, is_published=True)
        Product.objects.create(name='Скрытый костюм', slug='private-suit', category=cls.category, is_published=False)

    def test_home_category_selection_and_unknown_fallback(self):
        selected = self.client.get('/?collection=suits')
        self.assertEqual(selected.context['selected_collection'], 'suits')
        self.assertContains(selected, 'Открытый костюм')
        self.assertNotContains(selected, 'Скрытый костюм')
        self.assertEqual(self.client.get('/?collection=unknown').context['selected_collection'], 'all')

    def test_uploaded_look_video_is_in_fittings(self):
        look = Look.objects.create(title='Загруженное видео', slug='uploaded-film', video='videos/uploaded.mp4', is_published=True)
        response = self.client.get('/')
        self.assertIn(look, response.context['fittings'])
        self.assertContains(response, '/media/videos/uploaded.mp4')
        look.is_published = False
        look.save()
        self.assertNotContains(self.client.get('/'), '/media/videos/uploaded.mp4')

class DeploymentHealthTests(TestCase):
    @override_settings(DEPLOY_REVISION='b' * 40)
    def test_deployment_refreshes_css_and_js_urls(self):
        response = self.client.get('/')
        self.assertContains(response, '/static/css/site.css?v=' + 'b' * 40)
        self.assertContains(response, '/static/js/site.js?v=' + 'b' * 40)

    @override_settings(DEPLOY_REVISION='a' * 40)
    def test_health_reports_running_revision(self):
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'revision': 'a' * 40})
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_database_failure_is_unavailable_without_error_details(self):
        from unittest.mock import patch
        from django.db import DatabaseError
        with patch('config.health.connection.cursor', side_effect=DatabaseError('private details')):
            response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})
