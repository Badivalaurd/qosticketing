from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Project, Sprint, Epic, UserStory, Task, Deliverable, StoryComment


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
        self.fields['responsable'].queryset = it_members
        self.fields['responsable'].help_text = "Membre IT chargé de créer les tâches et suivre l'exécution."
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
            'color': forms.TextInput(attrs={'type': 'color', 'style': 'width:60px;height:38px;padding:2px;'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))


class UserStoryForm(forms.ModelForm):
    PRIORITY_CHOICES = [
        (0, '— Non défini —'),
        (1, '🔴 Critique'),
        (2, '🟠 Haute'),
        (3, '🟡 Normale'),
        (4, '🟢 Basse'),
    ]
    priority = forms.TypedChoiceField(
        choices=PRIORITY_CHOICES, coerce=int, label='Priorité', initial=0,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = UserStory
        fields = [
            'title', 'description', 'acceptance_criteria',
            'epic', 'sprint', 'assignee',
            'story_points', 'priority', 'status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'acceptance_criteria': forms.Textarea(attrs={'rows': 4}),
            'story_points': forms.NumberInput(attrs={'min': 0, 'max': 200}),
        }

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['epic'].queryset = Epic.objects.filter(project=project)
            self.fields['sprint'].queryset = Sprint.objects.filter(project=project).exclude(status='TERMINE')
            self.fields['assignee'].queryset = project.team.all().order_by('last_name', 'first_name')
        self.fields['epic'].required = False
        self.fields['epic'].empty_label = '— Aucun epic —'
        self.fields['sprint'].required = False
        self.fields['sprint'].empty_label = '— Backlog (pas de sprint) —'
        self.fields['assignee'].required = False
        self.fields['assignee'].empty_label = '— Non assigné —'
        if self.instance.pk:
            self.initial['priority'] = self.instance.priority
        self.helper = FormHelper()
        self.helper.form_tag = False


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'assignee', 'estimated_hours', 'actual_hours', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assignee'].queryset = project.team.all().order_by('last_name', 'first_name')
        self.fields['assignee'].required = False
        self.fields['assignee'].empty_label = '— Non assigné —'
        self.fields['actual_hours'].required = False
        self.helper = FormHelper()
        self.helper.form_tag = False


class StoryCommentForm(forms.ModelForm):
    class Meta:
        model = StoryComment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Ajouter un commentaire…',
                'class': 'form-control',
            }),
        }
        labels = {'body': ''}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


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
