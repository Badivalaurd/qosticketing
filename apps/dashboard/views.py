from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json


@login_required
def dashboard(request):
    from apps.tickets.models import Ticket
    from apps.accounts.models import User
    from apps.tickets.views import get_tickets_for_user

    user = request.user
    tickets_qs = get_tickets_for_user(user)

    now = timezone.now()

    # ---- KPI ----
    open_statuses = [
        Ticket.STATUS_NOUVEAU, Ticket.STATUS_AFFECTE,
        Ticket.STATUS_EN_COURS, Ticket.STATUS_ATTENTE_INFO, Ticket.STATUS_ATTENTE_PRESTATAIRE
    ]
    total_open = tickets_qs.filter(status__in=open_statuses).count()
    total_closed = tickets_qs.filter(status=Ticket.STATUS_CLOTURE).count()
    total_resolved = tickets_qs.filter(status=Ticket.STATUS_RESOLU).count()
    critical = tickets_qs.filter(
        priority=Ticket.PRIORITY_P0, status__in=open_statuses
    ).count()
    sla_exceeded = tickets_qs.filter(
        Q(sla_response_exceeded=True) | Q(sla_resolution_exceeded=True)
    ).filter(status__in=open_statuses).count()
    out_of_sla = tickets_qs.filter(resolved_out_of_sla=True).count()

    # Tickets assignés à moi (technicien / agent)
    my_open = tickets_qs.filter(
        assigned_to=user, status__in=open_statuses
    ).count() if user.can_process_tickets else 0

    # ---- Tickets récents ----
    recent_tickets = tickets_qs.select_related(
        'category', 'created_by', 'assigned_to'
    ).order_by('-created_at')[:10]

    # ---- Par statut ----
    by_status = {}
    for s, label in Ticket.STATUS_CHOICES:
        count = tickets_qs.filter(status=s).count()
        if count:
            by_status[label] = count

    # ---- Par catégorie ----
    by_category = list(
        tickets_qs.values('category__name').annotate(count=Count('id')).order_by('-count')[:6]
    )

    # ---- Par priorité ----
    by_priority = {}
    for p, label in Ticket.PRIORITY_CHOICES:
        by_priority[label] = tickets_qs.filter(priority=p).count()

    # ---- Tendance 14 jours ----
    trend_labels, trend_data = [], []
    for i in range(13, -1, -1):
        d = (now - timedelta(days=i)).date()
        trend_labels.append(d.strftime('%d/%m'))
        trend_data.append(tickets_qs.filter(created_at__date=d).count())

    # ---- Tickets en retard SLA ----
    overdue = tickets_qs.filter(
        Q(sla_response_deadline__lt=now) | Q(sla_resolution_deadline__lt=now)
    ).filter(status__in=open_statuses).order_by('sla_resolution_deadline')[:5]

    # ---- File d'attente agent (tickets NOUVEAU non affectés) ----
    agent_queue = []
    if user.role in [User.ROLE_ADMIN, User.ROLE_AGENT]:
        agent_queue = tickets_qs.filter(
            status=Ticket.STATUS_NOUVEAU, assigned_to=None
        ).order_by('priority', 'created_at')[:10]

    # ---- Mes tickets en cours (technicien) ----
    my_assigned = []
    if user.role == User.ROLE_TECHNICIEN:
        my_assigned = tickets_qs.filter(
            assigned_to=user, status__in=open_statuses
        ).order_by('-created_at')[:10]

    context = {
        'total_open': total_open,
        'total_closed': total_closed,
        'total_resolved': total_resolved,
        'critical': critical,
        'sla_exceeded': sla_exceeded,
        'out_of_sla': out_of_sla,
        'my_open': my_open,
        'recent_tickets': recent_tickets,
        'agent_queue': agent_queue,
        'my_assigned': my_assigned,
        'by_status_json': json.dumps(by_status),
        'by_category_json': json.dumps({d['category__name'] or 'N/A': d['count'] for d in by_category}),
        'by_priority_json': json.dumps(by_priority),
        'trend_labels_json': json.dumps(trend_labels),
        'trend_data_json': json.dumps(trend_data),
        'overdue_tickets': overdue,
    }
    return render(request, 'dashboard/dashboard.html', context)


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return redirect('account_login')
