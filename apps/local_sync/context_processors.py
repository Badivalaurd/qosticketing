"""
Context processors pour les templates : indicateurs hors-ligne.
"""


def offline_status(request):
    """Injecte pg_available et pending_count dans tous les templates."""
    pg_available = getattr(request, 'pg_available', True)

    pending_count = 0
    if request.user.is_authenticated:
        try:
            from apps.local_sync.models import PendingTicket
            pending_count = PendingTicket.objects.using('pending').filter(
                user_id=request.user.pk,
                sync_status=PendingTicket.SYNC_PENDING,
            ).count()
        except Exception:
            pass

    return {
        'pg_available': pg_available,
        'offline_pending_count': pending_count,
    }
