from pathlib import Path
from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError

def validate_image(file):
    if file.size > 8 * 1024 * 1024:
        raise ValidationError("Изображение должно быть не больше 8 МБ.")
    if Path(file.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValidationError("Загрузите JPEG, PNG или WebP.")
    try:
        file.open("rb")
        with Image.open(file) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValidationError("Загрузите JPEG, PNG или WebP.")
            if image.width * image.height > 40_000_000:
                raise ValidationError("Изображение слишком большое. Максимум — 40 мегапикселей.")
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValidationError("Файл повреждён или не является изображением.") from exc
    finally:
        if not file.closed:
            file.seek(0)


def validate_video(file):
    """Allow MP4 containers only; do not trust an extension or browser MIME type."""
    if file.size > 40 * 1024 * 1024:
        raise ValidationError("Видео должно быть не больше 40 МБ.")
    if Path(file.name).suffix.lower() != ".mp4":
        raise ValidationError("Загрузите MP4 (видео H.264, звук AAC).")
    try:
        file.open("rb")
        header = file.read(32)
        if len(header) < 16 or header[4:8] != b"ftyp" or int.from_bytes(header[:4], "big") < 16:
            raise ValidationError("Файл не является видео MP4.")
    finally:
        if not file.closed:
            file.seek(0)
