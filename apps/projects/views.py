from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from .models import Project, Sprint, Epic, UserStory, Task
from .forms import ProjectForm, SprintForm, EpicForm, UserStoryForm, TaskForm


def user_can_see_projects(user):
    """Membres du département IT OU membres d'au moins un projet."""
    if user.is_it_member:
        return True
    # Un utilisateur ajouté comme membre d'un projet peut y accéder
    return Project.objects.filter(team=user).exists()


def user_can_see_project(user, project):
    """Peut voir CE projet spécifique."""
    return user.is_it_member or project.team.filter(pk=user.pk).exists()


def user_can_create_project(user):
    """Seuls admin et agent de support du département Informatique."""
    from apps.accounts.models import User as U
    return user.is_it_member and user.role in [U.ROLE_ADMIN, U.ROLE_AGENT]


class ITRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return user_can_see_projects(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Accès réservé aux membres du département Informatique ou aux membres d'un projet.")
        return redirect('dashboard:home')


class ProjectListView(LoginRequiredMixin, ITRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        if user.is_it_member:
            # Membres IT voient tous les projets
            return Project.objects.all().select_related('manager', 'department')
        # Les autres ne voient que les projets dont ils sont membres
        return Project.objects.filter(team=user).select_related('manager', 'department')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_create'] = user_can_create_project(self.request.user)
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
        ctx['backlog'] = project.user_stories.filter(sprint=None).order_by('order')
        ctx['can_edit'] = user_can_create_project(user)
        ctx['is_it_member'] = user.is_it_member
        ctx['is_team_member'] = project.team.filter(pk=user.pk).exists()

        # Tâches assignées à l'utilisateur courant dans ce projet
        from .models import Task
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
        return user_can_create_project(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Seuls l'admin et l'agent de support peuvent créer un projet.")
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
        return user_can_create_project(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Modification non autorisée.")
        return redirect('projects:list')

    def form_valid(self, form):
        old_status = self.get_object().status
        response = super().form_valid(form)
        if form.instance.status != old_status:
            form.instance._status_changed = True
            form.instance.save(update_fields=['status'])
        return response


@login_required
def kanban_board(request, pk):
    if not user_can_see_projects(request.user):
        messages.error(request, "Accès réservé aux membres du département Informatique.")
        return redirect('dashboard:home')

    project = get_object_or_404(Project, pk=pk)
    sprint_id = request.GET.get('sprint')
    sprint = None
    stories_qs = project.user_stories.select_related('assignee', 'epic')
    if sprint_id:
        sprint = get_object_or_404(Sprint, pk=sprint_id, project=project)
        stories_qs = stories_qs.filter(sprint=sprint)

    columns = {
        status: {
            'label': label,
            'stories': stories_qs.filter(status=status).order_by('order'),
        }
        for status, label in UserStory.KANBAN_COLUMNS.items()
    }
    return render(request, 'projects/kanban.html', {
        'project': project,
        'columns': columns,
        'sprints': project.sprints.all(),
        'current_sprint': sprint,
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
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
def sprint_detail(request, project_pk, sprint_pk):
    if not user_can_see_projects(request.user):
        return redirect('dashboard:home')
    project = get_object_or_404(Project, pk=project_pk)
    sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
    stories = sprint.user_stories.select_related('assignee', 'epic').order_by('order')
    return render(request, 'projects/sprint_detail.html', {
        'project': project, 'sprint': sprint, 'stories': stories
    })


@login_required
def story_detail(request, project_pk, story_pk):
    if not user_can_see_projects(request.user):
        return redirect('dashboard:home')
    project = get_object_or_404(Project, pk=project_pk)
    story = get_object_or_404(UserStory, pk=story_pk, project=project)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.story = story
            task.save()
            messages.success(request, 'Tâche créée.')
            return redirect('projects:story_detail', project_pk=project_pk, story_pk=story_pk)
    else:
        form = TaskForm()
    return render(request, 'projects/story_detail.html', {
        'project': project, 'story': story,
        'tasks': story.tasks.all(), 'form': form
    })
