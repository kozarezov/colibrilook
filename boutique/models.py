from decimal import Decimal
from urllib.parse import urlencode
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.urls import reverse
from .validators import validate_image, validate_video

class PhotoMixin(models.Model):
    image = models.ImageField("Фотография", upload_to="photos/%Y/%m/", blank=True, validators=[validate_image])
    seed_image = models.CharField(max_length=160, blank=True, editable=False)
    image_alt = models.CharField("Описание фотографии", max_length=240, blank=True)

    class Meta:
        abstract = True

    @property
    def image_url(self):
        return self.image.url if self.image else (static(self.seed_image) if self.seed_image else "")

class VideoMixin(models.Model):
    video = models.FileField("Видео MP4", upload_to="videos/%Y/%m/", blank=True, validators=[validate_video], help_text="H.264 / AAC, до 40 МБ. Фото выше будет обложкой до воспроизведения.")
    seed_video = models.CharField(max_length=160, blank=True, editable=False)

    class Meta:
        abstract = True

    @property
    def video_url(self):
        return self.video.url if self.video else (static(self.seed_video) if self.seed_video else "")

class Category(models.Model):
    name = models.CharField("Название", max_length=80)
    slug = models.SlugField("Адрес в каталоге", unique=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показывать", default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Product(PhotoMixin, VideoMixin):
    card_focus = models.CharField("Кадрирование в каталоге", max_length=12, default="full", choices=[("full", "Весь образ"), ("top", "Верх"), ("bottom", "Брюки / лосины"), ("waist", "Деталь на талии")], help_text="Только обложка каталога; в галерее сохраняется полное фото.")
    class Availability(models.TextChoices):
        ASK = "ask", "Наличие уточняйте"
        AVAILABLE = "available", "В наличии"
        PREORDER = "preorder", "Предзаказ"
        SOLD = "sold", "Нет в наличии"

    name = models.CharField("Название", max_length=160)
    slug = models.SlugField("Адрес страницы", unique=True, max_length=180)
    category = models.ForeignKey(Category, verbose_name="Категория", on_delete=models.PROTECT, related_name="products")
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена, ₽", max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    sizes = models.CharField("Размеры", max_length=180, blank=True, help_text="Через запятую: S, M, L. Единый размер: 42–48.")
    colors = models.CharField("Цвета", max_length=180, blank=True)
    composition = models.CharField("Состав", max_length=250, blank=True)
    availability = models.CharField("Наличие", max_length=16, choices=Availability.choices, default=Availability.ASK)
    is_published = models.BooleanField("Опубликовано", default=False)
    is_featured = models.BooleanField("На главной", default=False)
    order = models.PositiveIntegerField("Порядок", default=0)
    source_url = models.URLField("Источник", blank=True)
    price_checked_at = models.DateField("Дата проверки цены", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "товар"
        verbose_name_plural = "Товары"
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0) | models.Q(price__isnull=True), name="product_positive_price")]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product", args=[self.slug])

    @property
    def option_label(self):
        return "Объём" if self.category.slug == "fragrance" else "Размер"

    @property
    def size_options(self):
        return [size.strip() for size in self.sizes.split(",") if size.strip()]

class ProductImage(PhotoMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="photos")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = "фотография"
        verbose_name_plural = "Галерея товара"

    def __str__(self):
        return self.image_alt or f"Фото: {self.product}"

class Look(PhotoMixin, VideoMixin):
    hero_image = models.ImageField("Главная: основной кадр", upload_to="covers/%Y/%m/", blank=True, validators=[validate_image])
    hero_detail = models.ImageField("Главная: второй кадр", upload_to="covers/%Y/%m/", blank=True, validators=[validate_image])
    seed_hero_image = models.CharField(max_length=160, blank=True, editable=False)
    seed_hero_detail = models.CharField(max_length=160, blank=True, editable=False)

    @property
    def hero_image_url(self):
        return self.hero_image.url if self.hero_image else (static(self.seed_hero_image) if self.seed_hero_image else self.image_url)

    @property
    def hero_detail_url(self):
        return self.hero_detail.url if self.hero_detail else (static(self.seed_hero_detail) if self.seed_hero_detail else "")

    on_home = models.BooleanField("В сцене на главной", default=False)
    title = models.CharField("Название", max_length=100)
    slug = models.SlugField("Адрес страницы", unique=True)
    description = models.TextField("Описание", blank=True)
    products = models.ManyToManyField(Product, verbose_name="Вещи в образе", blank=True, related_name="looks")
    is_published = models.BooleanField("Опубликовано", default=False)
    order = models.PositiveIntegerField("Порядок", default=0)
    source_url = models.URLField("Источник", blank=True)

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = "образ"
        verbose_name_plural = "Образы"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("look", args=[self.slug])

class Store(models.Model):
    name = models.CharField("Название бутика", max_length=100)
    address = models.CharField("Адрес", max_length=200)
    phone = models.CharField("Телефон", max_length=30)
    telegram = models.CharField("Telegram консультанта", max_length=40, validators=[RegexValidator(r"^[A-Za-z0-9_]{5,32}$", "Введите username без @ и ссылки.")])
    hours = models.CharField("Часы работы", max_length=150, default="Ежедневно, 10:00–21:00")
    map_url = models.URLField("Ссылка на карту")
    is_active = models.BooleanField("Показывать", default=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "pk"]
        verbose_name = "бутик"
        verbose_name_plural = "Бутики"

    def __str__(self):
        return self.name

    @property
    def phone_link(self):
        return "+" + "".join(c for c in self.phone if c.isdigit())

    @property
    def telegram_url(self):
        return f"https://t.me/{self.telegram}"

    def inquiry_url(self, product, size=""):
        message = f"Здравствуйте! Интересует {product.name}."
        if size:
            message += f" {product.option_label}: {size}."
        message += " Подскажите, пожалуйста, наличие и актуальную цену."
        if product.source_url:
            message += f"\n{product.source_url}"
        return f"{self.telegram_url}?{urlencode({'text': message})}"

class SiteSettings(PhotoMixin, VideoMixin):
    tagline = models.CharField("Подпись на первом экране", max_length=180, default="Одежда, в которой чувствуешь себя.")
    intro = models.CharField("Вступление", max_length=240, default="Готовые образы, аксессуары и парфюмерия. Два бутика в Краснодаре и ваш новый взгляд на себя.")
    about_title = models.CharField("Заголовок о бренде", max_length=80, default="Позволь себе больше")
    about_text = models.TextField("О бренде", default="Мы меняемся вместе с вами. В новом Colibri LOOK больше глубины, чувственности и смелости. Собираем вещи в образы, которые хочется примерить на себя.")
    telegram_url = models.URLField("Telegram-канал", default="https://t.me/colibri_look")
    instagram_url = models.URLField("Instagram", default="https://www.instagram.com/colibri_look_/")
    hero_look = models.ForeignKey(Look, verbose_name="Образ первого экрана", null=True, blank=True, on_delete=models.SET_NULL)
    seo_description = models.CharField("Описание для поиска", max_length=250, default="Colibri LOOK — бутики женской одежды в Краснодаре. Каталог вещей, готовые образы, аксессуары и парфюмерия. Уточните наличие в Telegram.")

    class Meta:
        verbose_name = "настройки сайта"
        verbose_name_plural = "Главная и настройки сайта"

    def __str__(self):
        return "Главная страница и контакты"

    def save(self, *args, **kwargs):
        if self._state.adding and SiteSettings.objects.exists():
            raise ValidationError("Настройки сайта уже созданы. Отредактируйте существующую запись.")
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.select_related("hero_look").first() or cls()
