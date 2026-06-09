from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Project, Sprint, Epic, UserStory, Task, Deliverable


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'code', 'description', 'status', 'responsable', 'team', 'department', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'team': forms.SelectMultiple(attrs={'size': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import User
        it_members = User.objects.filter(department__is_it_department=True, is_active=True).order_by('last_name', 'first_name')
        # Responsable d'exécution : tout membre IT actif
        self.fields['responsable'].queryset = it_members
        self.fields['responsable'].help_text = "Membre IT chargé de créer les tâches et suivre l'exécution."
        # Équipe invitée : membres IT + éventuellement d'autres départements
        self.fields['team'].queryset = User.objects.filter(is_active=True).order_by('department__name', 'last_name')
        self.fields['team'].help_text = "Tous les membres invités pourront consulter le projet."
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))


class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ['name', 'goal', 'status', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'goal': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))


class EpicForm(forms.ModelForm):
    class Meta:
        model = Epic
        fields = ['name', 'description', 'color', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class UserStoryForm(forms.ModelForm):
    class Meta:
        model = UserStory
        fields = ['title', 'description', 'acceptance_criteria', 'epic', 'sprint', 'assignee', 'story_points', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'acceptance_criteria': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['epic'].queryset = Epic.objects.filter(project=project)
            self.fields['sprint'].queryset = Sprint.objects.filter(project=project)
            self.fields['assignee'].queryset = project.team.all()
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'assignee', 'estimated_hours', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Ajouter', css_class='btn btn-sm btn-primary'))


class DeliverableForm(forms.ModelForm):
    class Meta:
        model = Deliverable
        fields = ['title', 'description', 'sprint', 'due_date', 'status']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['sprint'].queryset = Sprint.objects.filter(project=project)
        self.fields['sprint'].required = False
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))
