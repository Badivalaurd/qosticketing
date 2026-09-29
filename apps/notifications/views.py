from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notification_list(request):
    from django.core.paginator import Paginator
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'notifications/list.html', {
        'notifications': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    })


@login_required
@require_POST
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.mark_read()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.META.get('HTTP_REFERER') or reverse('notifications:list'))


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.META.get('HTTP_REFERER') or reverse('notifications:list'))
