"""Small deployment probe: verifies the running release and database connection."""
from django.conf import settings
from django.db import connection, DatabaseError
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except DatabaseError:
        response = JsonResponse({'status': 'unavailable'}, status=503)
    else:
        response = JsonResponse({'status': 'ok', 'revision': settings.DEPLOY_REVISION})
    response['Cache-Control'] = 'no-store'
    return response
