from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from .models import Ticket, Comment, Attachment, TicketHistory, Category, SubCategory, SLAConfig
from .forms import (
    TicketCreateForm, TicketEditForm, TicketAssignForm, TicketRequestInfoForm,
    TicketStatusForm, TicketPriorityForm, CommentForm, AttachmentForm, TicketFilterForm
)
from apps.notifications.utils import send_ticket_notification
from apps.accounts.models import User
import re


def get_tickets_for_user(user):
    """Retourne le queryset de tickets visibles pour l'utilisateur."""
    qs = Ticket.objects.select_related(
        'category', 'application', 'department', 'created_by', 'assigned_to', 'target_department'
    )

    # Admin, Agent, Technicien → tout voir
    if user.role in [User.ROLE_ADMIN, User.ROLE_AGENT, User.ROLE_TECHNICIEN]:
        return qs

    # Observateur IT → tout voir ; sinon son dept
    if user.role == User.ROLE_OBSERVATEUR:
        if user.is_it_member:
            return qs
        return qs.filter(department=user.department)

    # Manager → son département (cible ou demandeur)
    if user.role == User.ROLE_MANAGER:
        return qs.filter(
            Q(target_department=user.department) | Q(department=user.department)
        ).distinct()

    # Demandeur → tickets des membres de son département
    if user.role == User.ROLE_DEMANDEUR:
        if user.department:
            return qs.filter(created_by__department=user.department)
        return qs.filter(created_by=user)

    return qs.none()


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20

    def get_queryset(self):
        qs = get_tickets_for_user(self.request.user)
        form = self.filter_form
        if form.is_valid():
            d = form.cleaned_data
            if d.get('search'):
                qs = qs.filter(
                    Q(number__icontains=d['search']) |
                    Q(title__icontains=d['search']) |
                    Q(description__icontains=d['search'])
                )
            if d.get('status'):
                qs = qs.filter(status__in=d['status'])
            if d.get('priority'):
                qs = qs.filter(priority__in=d['priority'])
            if d.get('category'):
                qs = qs.filter(category=d['category'])
            if d.get('application'):
                qs = qs.filter(application=d['application'])
            if d.get('date_from'):
                qs = qs.filter(created_at__date__gte=d['date_from'])
            if d.get('date_to'):
                qs = qs.filter(created_at__date__lte=d['date_to'])
            if d.get('assigned_to_me'):
                qs = qs.filter(assigned_to=self.request.user)
            if d.get('sla_exceeded'):
                qs = qs.filter(Q(sla_response_exceeded=True) | Q(sla_resolution_exceeded=True))
            if d.get('out_of_sla'):
                qs = qs.filter(resolved_out_of_sla=True)
        return qs.order_by('-created_at')

    @property
    def filter_form(self):
        if not hasattr(self, '_filter_form'):
            self._filter_form = TicketFilterForm(self.request.GET or None)
        return self._filter_form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = self.filter_form
        ctx['total_count'] = self.get_queryset().count()
        return ctx


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_object(self):
        ticket = get_object_or_404(Ticket, number=self.kwargs['number'])
        if not ticket.can_user_see(self.request.user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return ticket

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        ctx = super().get_context_data(**kwargs)
        ticket = self.object
        user = self.request.user

        # Commentaires paginés (10 par page)
        show_internal = user.role != User.ROLE_DEMANDEUR
        comments_qs = (
            ticket.comments.all() if show_internal
            else ticket.comments.filter(is_internal=False)
        )
        comment_paginator = Paginator(comments_qs, 10)
        comment_page = self.request.GET.get('comment_page', 1)
        ctx['comments'] = comment_paginator.get_page(comment_page)
        ctx['comment_page_obj'] = ctx['comments']
        ctx['comment_is_paginated'] = comment_paginator.num_pages > 1

        # Historique paginé (15 par page)
        history_paginator = Paginator(ticket.history.order_by('-created_at'), 15)
        history_page = self.request.GET.get('history_page', 1)
        ctx['history'] = history_paginator.get_page(history_page)
        ctx['history_page_obj'] = ctx['history']
        ctx['history_is_paginated'] = history_paginator.num_pages > 1

        ctx['attachments'] = ticket.attachments.all()
        ctx['is_locked'] = ticket.is_locked

        # Ticket verrouillé — aucune action disponible
        if ticket.is_locked:
            ctx['allowed_transitions'] = []
            ctx['can_assign'] = False
            ctx['can_request_info'] = False
            ctx['can_change_priority'] = False
            ctx['can_set_waiting'] = False
            ctx['can_edit'] = False
            return ctx

        ctx['comment_form'] = CommentForm(user=user)
        ctx['attachment_form'] = AttachmentForm()
        ctx['allowed_transitions'] = ticket.get_allowed_transitions(user)
        ctx['status_form'] = TicketStatusForm(ticket=ticket, user=user)

        # Formulaire d'affectation (admin, agent, manager)
        can_assign = (
            user.role in [User.ROLE_ADMIN, User.ROLE_AGENT] or
            (user.role == User.ROLE_MANAGER and
             ticket.target_department and ticket.target_department == user.department)
        )
        ctx['can_assign'] = can_assign
        if can_assign:
            ctx['assign_form'] = TicketAssignForm(instance=ticket, current_user=user)

        # Formulaire demande d'info
        ctx['can_request_info'] = user.role in [User.ROLE_ADMIN, User.ROLE_AGENT, User.ROLE_TECHNICIEN, User.ROLE_MANAGER]
        if ctx['can_request_info'] and ticket.status == Ticket.STATUS_EN_COURS:
            ctx['request_info_form'] = TicketRequestInfoForm()

        # Redéfinition de priorité (admin et agent seulement, hors statuts terminaux)
        ctx['can_change_priority'] = (
            user.role in [User.ROLE_ADMIN, User.ROLE_AGENT] and
            ticket.status not in Ticket.SLA_STOP_STATUSES
        )
        if ctx['can_change_priority']:
            ctx['priority_form'] = TicketPriorityForm(ticket=ticket)

        ctx['can_set_waiting'] = user.role in [User.ROLE_ADMIN, User.ROLE_AGENT, User.ROLE_TECHNICIEN]

        ctx['can_edit'] = (
            user.role in [User.ROLE_ADMIN, User.ROLE_AGENT] or
            (ticket.status == Ticket.STATUS_NOUVEAU and ticket.created_by == user)
        )
        return ctx


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketCreateForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            if request.user.department and not ticket.department:
                ticket.department = request.user.department
            ticket.save()
            TicketHistory.objects.create(
                ticket=ticket, user=request.user,
                action=f"Ticket créé — statut '{ticket.get_status_display()}'"
            )
            files = request.FILES.getlist('files')
            for f in files:
                Attachment.objects.create(
                    ticket=ticket, file=f, filename=f.name,
                    file_size=f.size, content_type=f.content_type or '',
                    uploaded_by=request.user
                )
            send_ticket_notification(ticket, 'created')
            messages.success(request, f"Ticket {ticket.number} créé avec succès.")
            return redirect('tickets:detail', number=ticket.number)
    else:
        form = TicketCreateForm(user=request.user)
    return render(request, 'tickets/ticket_create.html', {'form': form})


@login_required
def ticket_edit(request, number):
    ticket = get_object_or_404(Ticket, number=number)
    if ticket.is_locked:
        messages.error(request, f"Ce ticket est {ticket.get_status_display().lower()} — aucune modification n'est possible.")
        return redirect('tickets:detail', number=number)
    if not (request.user.role in [User.ROLE_ADMIN, User.ROLE_AGENT] or
            (ticket.status == Ticket.STATUS_NOUVEAU and ticket.created_by == request.user)):
        messages.error(request, "Modification non autorisée.")
        return redirect('tickets:detail', number=number)

    if request.method == 'POST':
        form = TicketEditForm(request.POST, instance=ticket)
        if form.is_valid():
            old_vals = {f: getattr(ticket, f) for f in form.changed_data}
            ticket = form.save()
            for field in form.changed_data:
                TicketHistory.objects.create(
                    ticket=ticket, user=request.user,
                    action=f"Champ '{field}' modifié",
                    field_name=field,
                    old_value=str(old_vals.get(field, '')),
                    new_value=str(getattr(ticket, field, '')),
                )
            messages.success(request, "Ticket mis à jour.")
            return redirect('tickets:detail', number=number)
    else:
        form = TicketEditForm(instance=ticket)
    return render(request, 'tickets/ticket_edit.html', {'form': form, 'ticket': ticket})


@login_required
def ticket_change_status(request, number):
    ticket = get_object_or_404(Ticket, number=number)
    if ticket.is_locked:
        messages.error(request, f"Ce ticket est {ticket.get_status_display().lower()} — aucune modification n'est possible.")
        return redirect('tickets:detail', number=number)
    if not ticket.can_user_see(request.user):
        messages.error(request, "Accès non autorisé.")
        return redirect('tickets:list')

    if request.method == 'POST':
        form = TicketStatusForm(ticket=ticket, user=request.user, data=request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            comment_text = form.cleaned_data.get('comment', '')
            rejection_reason = form.cleaned_data.get('rejection_reason', '')
            old_status = ticket.status

            # Gérer les pauses/reprises SLA
            if old_status in Ticket.SLA_PAUSE_STATUSES and new_status not in Ticket.SLA_PAUSE_STATUSES:
                ticket.resume_sla()
            elif new_status in Ticket.SLA_PAUSE_STATUSES:
                ticket.pause_sla()

            ticket.status = new_status

            # Dates clés
            if new_status == Ticket.STATUS_AFFECTE and not ticket.assigned_at:
                ticket.assigned_at = timezone.now()
                # Vérifier SLA prise en charge
                if ticket.sla_response_deadline and timezone.now() > ticket.sla_response_deadline:
                    ticket.sla_response_exceeded = True

            if new_status == Ticket.STATUS_EN_COURS and not ticket.assigned_at:
                ticket.assigned_at = timezone.now()

            if new_status == Ticket.STATUS_RESOLU:
                ticket.resolved_at = timezone.now()
                if ticket.sla_resolution_deadline and timezone.now() > ticket.sla_resolution_deadline:
                    ticket.sla_resolution_exceeded = True
                    ticket.resolved_out_of_sla = True

            if new_status == Ticket.STATUS_CLOTURE:
                ticket.closed_at = timezone.now()

            if new_status == Ticket.STATUS_REJETE:
                ticket.rejection_reason = rejection_reason

            # Réouverture par demandeur → retour à NOUVEAU
            if old_status == Ticket.STATUS_RESOLU and new_status == Ticket.STATUS_NOUVEAU:
                ticket.resolved_at = None
                ticket.resolved_out_of_sla = False
                # Réinitialiser SLA
                ticket._init_sla()

            ticket.save()

            TicketHistory.objects.create(
                ticket=ticket, user=request.user,
                action=(
                    f"Statut : '{dict(Ticket.STATUS_CHOICES)[old_status]}'"
                    f" → '{dict(Ticket.STATUS_CHOICES)[new_status]}'"
                ),
                field_name='status', old_value=old_status, new_value=new_status,
            )
            if comment_text:
                Comment.objects.create(
                    ticket=ticket, author=request.user,
                    content=comment_text, is_internal=False
                )
            send_ticket_notification(ticket, 'status_changed')
            messages.success(request, f"Statut changé en '{ticket.get_status_display()}'.")
    return redirect('tickets:detail', number=number)


@login_required
def ticket_assign(request, number):
    ticket = get_object_or_404(Ticket, number=number)
    user = request.user

    if ticket.is_locked:
        messages.error(request, f"Ce ticket est {ticket.get_status_display().lower()} — aucune modification n'est possible.")
        return redirect('tickets:detail', number=number)

    can = (
        user.role in [User.ROLE_ADMIN, User.ROLE_AGENT] or
        (user.role == User.ROLE_MANAGER and
         ticket.target_department and ticket.target_department == user.department)
    )
    if not can:
        messages.error(request, "Affectation non autorisée.")
        return redirect('tickets:detail', number=number)

    if request.method == 'POST':
        form = TicketAssignForm(request.POST, instance=ticket, current_user=user)
        if form.is_valid():
            old_assignee = ticket.assigned_to
            ticket = form.save(commit=False)
            if ticket.assigned_to:
                # Réinitialisation SLA à chaque affectation/réaffectation (logique JIRA)
                ticket.reset_sla_on_assign()
                if ticket.status == Ticket.STATUS_NOUVEAU:
                    ticket.status = Ticket.STATUS_AFFECTE
            ticket.save()
            TicketHistory.objects.create(
                ticket=ticket, user=user,
                action=f"Affecté à {ticket.assigned_to} — SLA réinitialisé",
                field_name='assigned_to',
                old_value=str(old_assignee or ''),
                new_value=str(ticket.assigned_to or ''),
            )
            send_ticket_notification(ticket, 'assigned')
            messages.success(request, f"Ticket affecté à {ticket.assigned_to} — SLA réinitialisé.")
    return redirect('tickets:detail', number=number)


@login_required
def ticket_request_info(request, number):
    ticket = get_object_or_404(Ticket, number=number)
    if ticket.is_locked:
        return redirect('tickets:detail', number=number)
    if request.method == 'POST':
        form = TicketRequestInfoForm(request.POST)
        if form.is_valid():
            info_user = form.cleaned_data['info_requested_from']
            comment_text = form.cleaned_data['comment']
            old_status = ticket.status

            ticket.pause_sla()
            ticket.status = Ticket.STATUS_ATTENTE_INFO
            ticket.info_requested_from = info_user
            ticket.save()

            Comment.objects.create(
                ticket=ticket, author=request.user,
                content=f"@{info_user.username} — {comment_text}",
                is_internal=False
            )
            TicketHistory.objects.create(
                ticket=ticket, user=request.user,
                action=f"Demande d'information envoyée à {info_user.get_full_name() or info_user.username}",
                old_value=old_status, new_value=ticket.status,
            )
            send_ticket_notification(ticket, 'mentioned', recipient=info_user)
            messages.success(request, f"Demande d'information envoyée à {info_user}.")
    return redirect('tickets:detail', number=number)


@login_required
def add_comment(request, number):
    ticket = get_object_or_404(Ticket, number=number)
    if ticket.is_locked:
        messages.error(request, f"Ce ticket est {ticket.get_status_display().lower()} — les commentaires ne sont plus acceptés.")
        return redirect('tickets:detail', number=number)
    if not ticket.can_user_see(request.user):
        messages.error(request, "Accès non autorisé.")
        return redirect('tickets:list')

    if request.method == 'POST':
        user = request.user
        form = CommentForm(user=user, data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = user
            if user.role == User.ROLE_DEMANDEUR:
                comment.is_internal = False
            comment.save()
            # Mentions @username
            for username in re.findall(r'@(\w+)', comment.content):
                try:
                    mentioned = User.objects.get(username=username)
                    send_ticket_notification(ticket, 'mentioned', recipient=mentioned)
                except User.DoesNotExist:
                    pass
            TicketHistory.objects.create(ticket=ticket, user=user, action="Commentaire ajouté")
            send_ticket_notification(ticket, 'comment_added')
            messages.success(request, "Commentaire ajouté.")
    return redirect('tickets:detail', number=number)


@login_required
def add_attachment(request, number):
    ticket = get_object_or_404(Ticket, number=number)
    if ticket.is_locked:
        messages.error(request, f"Ce ticket est {ticket.get_status_display().lower()} — aucun ajout de pièce jointe n'est possible.")
        return redirect('tickets:detail', number=number)
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        for f in files:
            Attachment.objects.create(
                ticket=ticket, file=f, filename=f.name,
                file_size=f.size, content_type=f.content_type or '',
                uploaded_by=request.user
            )
            TicketHistory.objects.create(
                ticket=ticket, user=request.user,
                action=f"Pièce jointe : {f.name}"
            )
        messages.success(request, f"{len(files)} fichier(s) ajouté(s).")
    return redirect('tickets:detail', number=number)


@login_required
def ticket_change_priority(request, number):
    """Redéfinir la priorité d'un ticket et réinitialiser le SLA (admin/agent)."""
    ticket = get_object_or_404(Ticket, number=number)
    if ticket.is_locked:
        messages.error(request, f"Ce ticket est {ticket.get_status_display().lower()} — aucune modification n'est possible.")
        return redirect('tickets:detail', number=number)
    if request.user.role not in [User.ROLE_ADMIN, User.ROLE_AGENT]:
        messages.error(request, "Seuls l'admin et l'agent de support peuvent modifier la priorité.")
        return redirect('tickets:detail', number=number)

    if request.method == 'POST':
        form = TicketPriorityForm(ticket=ticket, data=request.POST)
        if form.is_valid():
            old_priority = ticket.get_priority_display()
            new_priority = form.cleaned_data['priority']
            reason = form.cleaned_data.get('reason', '')

            if new_priority != ticket.priority:
                ticket.reset_sla_for_priority(new_priority)
                ticket.save()

                comment_text = f"Priorité redéfinie : {old_priority} → {ticket.get_priority_display()}"
                if reason:
                    comment_text += f"\nMotif : {reason}"

                TicketHistory.objects.create(
                    ticket=ticket,
                    user=request.user,
                    action=comment_text,
                    field_name='priority',
                    old_value=old_priority,
                    new_value=ticket.get_priority_display(),
                )
                Comment.objects.create(
                    ticket=ticket, author=request.user,
                    content=comment_text, is_internal=True
                )
                messages.success(
                    request,
                    f"Priorité changée en {ticket.get_priority_display()} — SLA réinitialisé."
                )
            else:
                messages.info(request, "La priorité est déjà à ce niveau.")

    return redirect('tickets:detail', number=number)


@login_required
def subcategories_ajax(request):
    cat_id = request.GET.get('category_id')
    subs = SubCategory.objects.filter(category_id=cat_id, is_active=True).values('id', 'name')
    return JsonResponse({'subcategories': list(subs)})


@login_required
def my_tickets(request):
    from django.core.paginator import Paginator
    if request.user.role == User.ROLE_DEMANDEUR:
        qs = Ticket.objects.filter(created_by=request.user)
    else:
        qs = Ticket.objects.filter(assigned_to=request.user)
    qs = qs.select_related('category', 'application', 'assigned_to', 'created_by').order_by('-created_at')
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'tickets/my_tickets.html', {
        'tickets': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    })


@login_required
def sla_config_view(request):
    """Page de configuration SLA (admin seulement)."""
    if request.user.role != User.ROLE_ADMIN:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard:home')

    # S'assurer que toutes les configs existent
    configs = {c.priority: c for c in SLAConfig.objects.all()}
    for priority, defaults in SLAConfig.DEFAULTS.items():
        if priority not in configs:
            obj = SLAConfig.objects.create(
                priority=priority,
                response_time_minutes=defaults['response'],
                resolution_time_minutes=defaults['resolution'],
            )
            configs[priority] = obj

    if request.method == 'POST':
        errors = []
        for priority, cfg in configs.items():
            try:
                response = int(request.POST.get(f'{priority}-response_time_minutes', 0))
                resolution = int(request.POST.get(f'{priority}-resolution_time_minutes', 0))
                if response > 0 and resolution > 0:
                    cfg.response_time_minutes = response
                    cfg.resolution_time_minutes = resolution
                    cfg.save()
                else:
                    errors.append(f"{priority}: les valeurs doivent être supérieures à 0")
            except (ValueError, TypeError):
                errors.append(f"{priority}: valeurs non numériques")
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            messages.success(request, "Configuration SLA enregistrée avec succès.")
        return redirect('tickets:sla_config')

    # Construire la liste pour le template
    priority_order = [SLAConfig.P0, SLAConfig.P1, SLAConfig.P2, SLAConfig.P3]
    sla_items = [
        {
            'priority': p,
            'label': configs[p].get_priority_display(),
            'config': configs[p],
        }
        for p in priority_order if p in configs
    ]

    return render(request, 'tickets/sla_config.html', {'sla_items': sla_items})
