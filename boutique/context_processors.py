from .models import SiteSettings, Store
from django.conf import settings

def site_content(request):
    return {"site": SiteSettings.load(), "stores": Store.objects.filter(is_active=True),
            "asset_revision": settings.DEPLOY_REVISION}
