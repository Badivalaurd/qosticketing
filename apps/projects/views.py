from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from .models import Project, Sprint, Epic, UserStory, Task, Deliverable, StoryComment
from .forms import (
    ProjectForm, SprintForm, EpicForm, UserStoryForm,
    TaskForm, DeliverableForm, StoryCommentForm,
)

PRIORITY_LABELS = {0: '—', 1: 'Critique', 2: 'Haute', 3: 'Normale', 4: 'Basse'}
PRIORITY_COLORS = {0: 'secondary', 1: 'danger', 2: 'warning', 3: 'primary', 4: 'success'}


def user_can_see_projects(user):
    return user.is_it_member or user.is_admin


def user_can_see_project(user, project):
    return user.is_it_member or user.is_admin or project.team.filter(pk=user.pk).exists()


def user_can_manage_project(user, project=None):
    return user.can_manage_projects


def user_can_execute_project(user, project):
    return (
        user.can_manage_projects or
        (project.responsable_id and project.responsable_id == user.pk) or
        user.is_admin
    )


class ITRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return user_can_see_projects(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Accès réservé aux membres du département Informatique.")
        return redirect('dashboard:home')


# ── Project CRUD ──────────────────────────────────────────────────────────────

class ProjectListView(LoginRequiredMixin, ITRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        if user.is_it_member:
            return Project.objects.all().select_related('manager', 'department')
        return Project.objects.filter(team=user).select_related('manager', 'department')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_create'] = user_can_manage_project(self.request.user)
        return ctx


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'

    def get_object(self):
        project = super().get_object()
        if not user_can_see_project(self.request.user, project):
            raise PermissionDenied
        return project

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user
        ctx['sprints'] = project.sprints.all()
        ctx['epics'] = project.epics.all()
        ctx['backlog'] = project.user_stories.filter(sprint=None).select_related('assignee', 'epic').order_by('priority', 'order')
        ctx['deliverables'] = project.deliverables.select_related('sprint').order_by('due_date')
        ctx['can_manage'] = user_can_manage_project(user, project)
        ctx['can_execute'] = user_can_execute_project(user, project)
        ctx['is_it_member'] = user.is_it_member
        ctx['is_team_member'] = project.team.filter(pk=user.pk).exists()
        ctx['PRIORITY_LABELS'] = PRIORITY_LABELS
        ctx['PRIORITY_COLORS'] = PRIORITY_COLORS

        ctx['my_tasks'] = Task.objects.filter(
            story__project=project, assignee=user
        ).select_related('story').order_by('story__title', 'order')

        ctx['stats'] = {
            'total': project.user_stories.count(),
            'done': project.user_stories.filter(status='DONE').count(),
            'in_progress': project.user_stories.filter(status='IN_PROGRESS').count(),
            'points': sum(s.story_points for s in project.user_stories.all()),
        }
        return ctx


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')

    def test_func(self):
        return user_can_manage_project(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Seuls les chefs de projet IT peuvent créer un projet.")
        return redirect('projects:list')

    def form_valid(self, form):
        form.instance.manager = self.request.user
        messages.success(self.request, 'Projet créé avec succès.')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')

    def test_func(self):
        return user_can_manage_project(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Modification réservée aux chefs de projet IT.")
        return redirect('projects:list')

    def form_valid(self, form):
        messages.success(self.request, 'Projet mis à jour.')
        return super().form_valid(form)


# ── Kanban & Gantt ────────────────────────────────────────────────────────────

@login_required
def kanban_board(request, pk):
    if not user_can_see_projects(request.user):
        messages.error(request, "Accès réservé aux membres du département Informatique.")
        return redirect('dashboard:home')

    project = get_object_or_404(Project, pk=pk)
    sprint_id = request.GET.get('sprint')
    epic_id = request.GET.get('epic')
    sprint = None
    stories_qs = project.user_stories.select_related('assignee', 'epic')
    if sprint_id:
        sprint = get_object_or_404(Sprint, pk=sprint_id, project=project)
        stories_qs = stories_qs.filter(sprint=sprint)
    if epic_id:
        stories_qs = stories_qs.filter(epic_id=epic_id)

    columns = {
        status: {
            'label': label,
            'stories': list(stories_qs.filter(status=status).order_by('order')),
        }
        for status, label in UserStory.KANBAN_COLUMNS.items()
    }
    return render(request, 'projects/kanban.html', {
        'project': project,
        'columns': columns,
        'sprints': project.sprints.all(),
        'epics': project.epics.all(),
        'current_sprint': sprint,
        'current_epic_id': epic_id,
        'can_execute': user_can_execute_project(request.user, project),
        'PRIORITY_LABELS': PRIORITY_LABELS,
        'PRIORITY_COLORS': PRIORITY_COLORS,
    })


@login_required
def gantt_view(request, pk):
    if not user_can_see_projects(request.user):
        messages.error(request, "Accès réservé aux membres du département Informatique.")
        return redirect('dashboard:home')

    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/gantt.html', {
        'project': project,
        'epics': project.epics.all(),
        'stories': project.user_stories.filter(sprint__isnull=False).select_related('sprint', 'epic').order_by('sprint__start_date'),
        'sprints': project.sprints.all().order_by('start_date'),
    })


# ── Backlog / Sprint Planning ─────────────────────────────────────────────────

@login_required
def backlog_view(request, pk):
    if not user_can_see_projects(request.user):
        messages.error(request, "Accès réservé aux membres du département Informatique.")
        return redirect('dashboard:home')

    project = get_object_or_404(Project, pk=pk)
    if not user_can_see_project(request.user, project):
        raise PermissionDenied

    sprints = project.sprints.exclude(status='TERMINE').order_by('start_date')
    backlog_stories = (
        project.user_stories
        .filter(sprint=None)
        .select_related('assignee', 'epic')
        .order_by('priority', 'order', '-created_at')
    )
    sprint_stories = {
        s.pk: list(s.user_stories.select_related('assignee', 'epic').order_by('priority', 'order'))
        for s in sprints
    }

    return render(request, 'projects/backlog.html', {
        'project': project,
        'sprints': sprints,
        'backlog_stories': backlog_stories,
        'sprint_stories': sprint_stories,
        'can_manage': user_can_manage_project(request.user, project),
        'can_execute': user_can_execute_project(request.user, project),
        'PRIORITY_LABELS': PRIORITY_LABELS,
        'PRIORITY_COLORS': PRIORITY_COLORS,
    })


# ── AJAX story status ─────────────────────────────────────────────────────────

@login_required
@require_POST
def update_story_status(request, pk):
    if not user_can_see_projects(request.user):
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    story = get_object_or_404(UserStory, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(UserStory.STATUS_CHOICES):
        story.status = new_status
        story.save()
        return JsonResponse({'success': True, 'new_status': new_status})
    return JsonResponse({'success': False}, status=400)


@login_required
@require_POST
def story_move_sprint(request, project_pk, story_pk):
    project = get_object_or_404(Project, pk=project_pk)
    story = get_object_or_404(UserStory, pk=story_pk, project=project)
    if not user_can_execute_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:backlog', pk=project_pk)

    sprint_id = request.POST.get('sprint_id') or None
    if sprint_id:
        sprint = get_object_or_404(Sprint, pk=sprint_id, project=project)
        story.sprint = sprint
        if story.status == UserStory.STATUS_BACKLOG:
            story.status = UserStory.STATUS_TODO
    else:
        story.sprint = None
        story.status = UserStory.STATUS_BACKLOG
    story.save()
    messages.success(request, 'Story déplacée.')
    return redirect('projects:backlog', pk=project_pk)


# ── Sprint CRUD & Lifecycle ───────────────────────────────────────────────────

@login_required
def sprint_detail(request, project_pk, sprint_pk):
    if not user_can_see_projects(request.user):
        return redirect('dashboard:home')
    project = get_object_or_404(Project, pk=project_pk)
    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
    stories = sprint.user_stories.select_related('assignee', 'epic').order_by('priority', 'order')
    total = stories.count()
    done = stories.filter(status='DONE').count()
    progress = int(done * 100 / total) if total else 0
    return render(request, 'projects/sprint_detail.html', {
        'project': project, 'sprint': sprint, 'stories': stories,
        'progress': progress, 'total': total, 'done': done,
        'can_manage': user_can_manage_project(request.user, project),
        'can_execute': user_can_execute_project(request.user, project),
        'PRIORITY_LABELS': PRIORITY_LABELS,
        'PRIORITY_COLORS': PRIORITY_COLORS,
    })


@login_required
def sprint_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Seul le chef de projet peut créer des sprints.")
        return redirect('projects:detail', pk=project_pk)

    if request.method == 'POST':
        form = SprintForm(request.POST)
        if form.is_valid():
            sprint = form.save(commit=False)
            sprint.project = project
            sprint.save()
            messages.success(request, f'Sprint « {sprint.name} » créé.')
            return redirect('projects:detail', pk=project_pk)
    else:
        form = SprintForm()
    return render(request, 'projects/sprint_form.html', {'form': form, 'project': project, 'action': 'Créer'})


@login_required
def sprint_update(request, project_pk, sprint_pk):
    project = get_object_or_404(Project, pk=project_pk)
    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Modification réservée au chef de projet.")
        return redirect('projects:detail', pk=project_pk)

    if request.method == 'POST':
        form = SprintForm(request.POST, instance=sprint)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sprint mis à jour.')
            return redirect('projects:sprint_detail', project_pk=project_pk, sprint_pk=sprint_pk)
    else:
        form = SprintForm(instance=sprint)
    return render(request, 'projects/sprint_form.html', {'form': form, 'project': project, 'sprint': sprint, 'action': 'Modifier'})


@login_required
@require_POST
def sprint_start(request, project_pk, sprint_pk):
    project = get_object_or_404(Project, pk=project_pk)
    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:sprint_detail', project_pk=project_pk, sprint_pk=sprint_pk)
    sprint.status = Sprint.STATUS_ACTIF
    sprint.save()
    messages.success(request, f'Sprint « {sprint.name} » démarré.')
    return redirect('projects:sprint_detail', project_pk=project_pk, sprint_pk=sprint_pk)


@login_required
@require_POST
def sprint_complete(request, project_pk, sprint_pk):
    project = get_object_or_404(Project, pk=project_pk)
    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:sprint_detail', project_pk=project_pk, sprint_pk=sprint_pk)
    unfinished = sprint.user_stories.exclude(status='DONE')
    count = unfinished.count()
    unfinished.update(sprint=None, status=UserStory.STATUS_BACKLOG)
    sprint.status = Sprint.STATUS_TERMINE
    sprint.save()
    msg = f'Sprint « {sprint.name} » clôturé.'
    if count:
        msg += f' {count} story(ies) renvoyée(s) au backlog.'
    messages.success(request, msg)
    return redirect('projects:detail', pk=project_pk)


@login_required
@require_POST
def sprint_delete(request, project_pk, sprint_pk):
    project = get_object_or_404(Project, pk=project_pk)
    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:detail', pk=project_pk)
    sprint.user_stories.update(sprint=None, status=UserStory.STATUS_BACKLOG)
    sprint.delete()
    messages.success(request, 'Sprint supprimé.')
    return redirect('projects:detail', pk=project_pk)


# ── Epic CRUD ─────────────────────────────────────────────────────────────────

@login_required
def epic_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not user_can_execute_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:detail', pk=project_pk)

    if request.method == 'POST':
        form = EpicForm(request.POST)
        if form.is_valid():
            epic = form.save(commit=False)
            epic.project = project
            epic.save()
            messages.success(request, f'Epic « {epic.name} » créé.')
            return redirect('projects:detail', pk=project_pk)
    else:
        form = EpicForm()
    return render(request, 'projects/epic_form.html', {'form': form, 'project': project, 'action': 'Créer'})


@login_required
def epic_update(request, project_pk, epic_pk):
    project = get_object_or_404(Project, pk=project_pk)
    epic = get_object_or_404(Epic, pk=epic_pk, project=project)
    if not user_can_execute_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:detail', pk=project_pk)

    if request.method == 'POST':
        form = EpicForm(request.POST, instance=epic)
        if form.is_valid():
            form.save()
            messages.success(request, 'Epic mis à jour.')
            return redirect('projects:detail', pk=project_pk)
    else:
        form = EpicForm(instance=epic)
    return render(request, 'projects/epic_form.html', {'form': form, 'project': project, 'epic': epic, 'action': 'Modifier'})


@login_required
@require_POST
def epic_delete(request, project_pk, epic_pk):
    project = get_object_or_404(Project, pk=project_pk)
    epic = get_object_or_404(Epic, pk=epic_pk, project=project)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:detail', pk=project_pk)
    epic.delete()
    messages.success(request, 'Epic supprimé.')
    return redirect('projects:detail', pk=project_pk)


# ── User Story CRUD ───────────────────────────────────────────────────────────

@login_required
def story_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not user_can_execute_project(request.user, project):
        messages.error(request, "Seul le responsable d'exécution peut créer des stories.")
        return redirect('projects:detail', pk=project_pk)

    sprint_pk = request.GET.get('sprint')
    status_init = request.GET.get('status', 'BACKLOG')
    initial = {'status': 'TODO' if sprint_pk else status_init}
    if sprint_pk:
        initial['sprint'] = sprint_pk

    if request.method == 'POST':
        form = UserStoryForm(project, request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.project = project
            story.save()
            messages.success(request, f'Story « {story.title} » créée.')
            return redirect('projects:story_detail', project_pk=project_pk, story_pk=story.pk)
    else:
        form = UserStoryForm(project, initial=initial)

    return render(request, 'projects/story_form.html', {
        'form': form, 'project': project, 'action': 'Créer'
    })


@login_required
def story_update(request, project_pk, story_pk):
    project = get_object_or_404(Project, pk=project_pk)
    story = get_object_or_404(UserStory, pk=story_pk, project=project)
    if not user_can_execute_project(request.user, project):
        messages.error(request, "Seul le responsable d'exécution peut modifier des stories.")
        return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)

    if request.method == 'POST':
        form = UserStoryForm(project, request.POST, instance=story)
        if form.is_valid():
            form.save()
            messages.success(request, 'Story mise à jour.')
            return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)
    else:
        form = UserStoryForm(project, instance=story)

    return render(request, 'projects/story_form.html', {
        'form': form, 'project': project, 'story': story, 'action': 'Modifier'
    })


@login_required
@require_POST
def story_delete(request, project_pk, story_pk):
    project = get_object_or_404(Project, pk=project_pk)
    story = get_object_or_404(UserStory, pk=story_pk, project=project)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)
    story.delete()
    messages.success(request, 'Story supprimée.')
    return redirect('projects:detail', pk=project_pk)


@login_required
def story_detail(request, project_pk, story_pk):
    if not user_can_see_projects(request.user):
        return redirect('dashboard:home')
    project = get_object_or_404(Project, pk=project_pk)
    story = get_object_or_404(UserStory, pk=story_pk, project=project)
    can_execute = user_can_execute_project(request.user, project)
    can_manage = user_can_manage_project(request.user, project)

    if request.method == 'POST':
        if not can_execute:
            messages.error(request, "Seul le responsable d'exécution peut créer des tâches.")
            return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.story = story
            task.save()
            messages.success(request, 'Tâche créée.')
            return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)
    else:
        form = TaskForm(project=project)

    return render(request, 'projects/story_detail.html', {
        'project': project,
        'story': story,
        'tasks': story.tasks.select_related('assignee').order_by('order', 'created_at'),
        'comments': story.comments.select_related('author').order_by('created_at'),
        'comment_form': StoryCommentForm(),
        'task_form': form,
        'can_execute': can_execute,
        'can_manage': can_manage,
        'PRIORITY_LABELS': PRIORITY_LABELS,
        'PRIORITY_COLORS': PRIORITY_COLORS,
    })


@login_required
@require_POST
def story_comment_add(request, project_pk, story_pk):
    project = get_object_or_404(Project, pk=project_pk)
    story = get_object_or_404(UserStory, pk=story_pk, project=project)
    if not user_can_see_project(request.user, project):
        raise PermissionDenied
    form = StoryCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.story = story
        comment.author = request.user
        comment.save()
        messages.success(request, 'Commentaire ajouté.')
    return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)


# ── Task CRUD ─────────────────────────────────────────────────────────────────

@login_required
def task_update(request, project_pk, task_pk):
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_pk, story__project=project)
    if not user_can_execute_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:story_detail', project_pk=project_pk, story_pk=task.story.pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tâche mise à jour.')
            return redirect('projects:story_detail', project_pk=project_pk, story_pk=task.story.pk)
    else:
        form = TaskForm(instance=task, project=project)

    return render(request, 'projects/task_form.html', {
        'form': form, 'project': project, 'task': task, 'story': task.story, 'action': 'Modifier'
    })


@login_required
@require_POST
def task_delete(request, project_pk, task_pk):
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_pk, story__project=project)
    if not user_can_execute_project(request.user, project):
        messages.error(request, "Non autorisé.")
        return redirect('projects:story_detail', project_pk=project_pk, story_pk=task.story.pk)
    story_pk = task.story.pk
    task.delete()
    messages.success(request, 'Tâche supprimée.')
    return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)


@login_required
@require_POST
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not user_can_see_projects(request.user):
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    new_status = request.POST.get('status')
    if new_status in dict(Task.STATUS_CHOICES):
        task.status = new_status
        task.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# ── Deliverable CRUD ──────────────────────────────────────────────────────────

@login_required
def deliverable_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Seul le chef de projet peut définir les livrables.")
        return redirect('projects:detail', pk=project_pk)

    if request.method == 'POST':
        form = DeliverableForm(request.POST, project=project)
        if form.is_valid():
            deliverable = form.save(commit=False)
            deliverable.project = project
            deliverable.save()
            messages.success(request, f'Livrable « {deliverable.title} » créé.')
            return redirect('projects:detail', pk=project_pk)
    else:
        form = DeliverableForm(project=project)
    return render(request, 'projects/deliverable_form.html', {'form': form, 'project': project, 'action': 'Créer'})


@login_required
def deliverable_update(request, project_pk, deliverable_pk):
    project = get_object_or_404(Project, pk=project_pk)
    deliverable = get_object_or_404(Deliverable, pk=deliverable_pk, project=project)
    if not user_can_manage_project(request.user, project):
        messages.error(request, "Modification réservée au chef de projet.")
        return redirect('projects:detail', pk=project_pk)

    if request.method == 'POST':
        form = DeliverableForm(request.POST, instance=deliverable, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Livrable mis à jour.')
            return redirect('projects:detail', pk=project_pk)
    else:
        form = DeliverableForm(instance=deliverable, project=project)
    return render(request, 'projects/deliverable_form.html', {'form': form, 'project': project, 'deliverable': deliverable, 'action': 'Modifier'})
