from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    recent = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent,
    }
