"""REG.RU startup file: shared configuration, atomic release selection."""
import os
import site
import sys
from pathlib import Path

APP_ROOT = Path('/var/www/u3688705/data/apps/colibri')
RELEASE = (APP_ROOT / 'current').resolve() if (APP_ROOT / 'current').is_symlink() else APP_ROOT
sys.path.insert(0, str(RELEASE))
site.addsitedir(str(RELEASE / '.venv/lib/python3.14/site-packages'))
os.environ.setdefault('DJANGO_ENV_FILE', str(APP_ROOT / 'production.json'))
os.environ.setdefault('DJANGO_MEDIA_ROOT', str(APP_ROOT / 'media'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
