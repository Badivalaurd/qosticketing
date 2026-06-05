from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div
from .models import Ticket, Comment, Attachment, Category, SubCategory, Application, SLAConfig


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'sub_category', 'application',
                  'department', 'target_department', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'title': forms.TextInput(attrs={'placeholder': 'Titre court et descriptif'}),
        }
        labels = {
            'title': 'Titre',
            'description': 'Description détaillée',
            'category': 'Catégorie',
            'sub_category': 'Sous-catégorie',
            'application': 'Application concernée',
            'department': 'Département demandeur',
            'target_department': 'Envoyer vers un autre département',
            'priority': 'Priorité',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Sous-catégories
        self.fields['sub_category'].queryset = SubCategory.objects.none()
        if 'category' in self.data:
            try:
                cat_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = SubCategory.objects.filter(
                    category_id=cat_id, is_active=True
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category_id:
            self.fields['sub_category'].queryset = SubCategory.objects.filter(
                category=self.instance.category, is_active=True
            )

        # Département du demandeur : pré-rempli depuis le compte, non modifiable
        from apps.accounts.models import Department
        if user and user.department:
            self.fields['department'].initial = user.department
            self.fields['department'].queryset = Department.objects.filter(pk=user.department.pk)
            self.fields['department'].widget.attrs['disabled'] = True
        self.fields['department'].required = False  # la vue le fixe depuis user.department

        # Département cible : uniquement les depts activés par l'admin (non-IT)
        enabled_depts = Department.objects.filter(
            ticketing_enabled=True, is_it_department=False, is_active=True
        )
        self.fields['target_department'].queryset = enabled_depts
        self.fields['target_department'].required = False
        self._has_target_depts = enabled_depts.exists()

        if self._has_target_depts:
            self.fields['target_department'].help_text = (
                "Laissez vide pour envoyer à l'équipe support IT. "
                "Sélectionnez un département si votre demande concerne un autre service."
            )

        # Construction du layout selon les depts disponibles
        self.helper = FormHelper()
        dept_row = (
            Row(
                Column('department', css_class='col-md-6'),
                Column('target_department', css_class='col-md-6'),
            )
            if self._has_target_depts else 'department'
        )
        self.helper.layout = Layout(
            'title',
            Row(
                Column('category', css_class='col-md-6'),
                Column('sub_category', css_class='col-md-6'),
            ),
            Row(
                Column('application', css_class='col-md-6'),
                Column('priority', css_class='col-md-6'),
            ),
            dept_row,
            'description',
            Submit('submit', 'Créer le ticket', css_class='btn btn-primary'),
        )


class TicketEditForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'sub_category', 'application', 'department', 'priority']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.category_id:
            self.fields['sub_category'].queryset = SubCategory.objects.filter(
                category=self.instance.category
            )
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))


class TicketAssignForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['assigned_to']
        labels = {'assigned_to': 'Assigner à'}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        from apps.accounts.models import User
        ticket = self.instance

        # Rôles non affectables : Admin, Agent de Support, Observateur
        EXCLUDED_ROLES = [User.ROLE_ADMIN, User.ROLE_AGENT, User.ROLE_OBSERVATEUR]

        if user and user.role == User.ROLE_ADMIN:
            # Admin : tout le monde sauf admin, agent, observateur
            qs = User.objects.filter(is_active=True).exclude(role__in=EXCLUDED_ROLES)

        elif user and user.role == User.ROLE_AGENT:
            # Agent : membres de son département (hors rôles exclus)
            qs = User.objects.filter(
                department=user.department,
                is_active=True
            ).exclude(pk=user.pk).exclude(role__in=EXCLUDED_ROLES)

        elif user and user.role == User.ROLE_MANAGER:
            # Manager : membres de son département (hors rôles exclus)
            qs = User.objects.filter(
                department=user.department,
                is_active=True
            ).exclude(pk=user.pk).exclude(role__in=EXCLUDED_ROLES)

        else:
            qs = User.objects.none()

        self.fields['assigned_to'].queryset = qs.order_by('last_name', 'first_name')
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Affecter', css_class='btn btn-primary btn-sm'))


class TicketRequestInfoForm(forms.Form):
    """Formulaire pour envoyer en demande d'information."""
    info_requested_from = forms.ModelChoiceField(
        label='Demander l\'information à',
        queryset=None,
        help_text='Les administrateurs ne peuvent pas être destinataires d\'une demande d\'info.'
    )
    comment = forms.CharField(
        label='Message / Question',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import User
        # Les admins sont exclus : ils ne reçoivent pas de demandes d'info
        self.fields['info_requested_from'].queryset = User.objects.filter(
            is_active=True
        ).exclude(role=User.ROLE_ADMIN).order_by('last_name', 'first_name')
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Envoyer la demande', css_class='btn btn-warning btn-sm'))


class TicketRespondInfoForm(forms.Form):
    """Formulaire utilisé par info_requested_from pour répondre à la demande."""
    response = forms.CharField(
        label='Votre réponse',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Répondez ici à la demande d\'information...'
        }),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Envoyer ma réponse', css_class='btn btn-success btn-sm'))


class TicketTransferDeptForm(forms.Form):
    """Formulaire de transfert d'un ticket vers un autre département activé (agent/admin)."""
    target_department = forms.ModelChoiceField(
        label='Département cible',
        queryset=None,
        help_text='Ce ticket sera transmis au manager de ce département pour distribution.'
    )
    comment = forms.CharField(
        label='Motif du transfert',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Expliquer pourquoi ce ticket est transféré...'}),
        required=False
    )

    def __init__(self, *args, exclude_dept=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import Department
        qs = Department.objects.filter(ticketing_enabled=True, is_it_department=False, is_active=True)
        if exclude_dept:
            qs = qs.exclude(pk=exclude_dept.pk)
        self.fields['target_department'].queryset = qs.order_by('name')
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Transférer', css_class='btn btn-info btn-sm'))


class TicketStatusForm(forms.Form):
    new_status = forms.ChoiceField(label='Nouveau statut', choices=[])
    comment = forms.CharField(
        label='Commentaire',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    rejection_reason = forms.CharField(
        label='Motif de rejet',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    def __init__(self, ticket, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = ticket.get_allowed_transitions(user)
        self.fields['new_status'].choices = [
            (s, dict(Ticket.STATUS_CHOICES).get(s, s)) for s in allowed
        ]
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Changer le statut', css_class='btn btn-warning btn-sm'))


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'is_internal']
        widgets = {'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Votre commentaire...'})}
        labels = {
            'content': 'Commentaire',
            'is_internal': 'Commentaire interne (non visible par le demandeur)',
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import User
        if user and user.role == User.ROLE_DEMANDEUR:
            del self.fields['is_internal']
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'content',
            'is_internal' if 'is_internal' in self.fields else Div(),
            Submit('submit', 'Ajouter', css_class='btn btn-primary btn-sm'),
        )


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']
        labels = {'file': 'Fichier (PDF, Excel, Word, Image, Log)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs['accept'] = (
            '.pdf,.xls,.xlsx,.doc,.docx,.png,.jpg,.jpeg,.gif,.txt,.log,.csv'
        )


class TicketPriorityForm(forms.Form):
    """Formulaire de redéfinition de priorité par l'agent (réinitialise le SLA)."""
    priority = forms.ChoiceField(
        label='Nouvelle priorité',
        choices=Ticket.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    reason = forms.CharField(
        label='Motif du changement',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Expliquer pourquoi la priorité est redéfinie...'}),
        required=False,
    )

    def __init__(self, ticket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['priority'].initial = ticket.priority
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Appliquer', css_class='btn btn-warning btn-sm'))


class SLAConfigForm(forms.ModelForm):
    class Meta:
        model = SLAConfig
        fields = ['response_time_minutes', 'resolution_time_minutes']
        labels = {
            'response_time_minutes': 'Délai prise en charge (minutes)',
            'resolution_time_minutes': 'Délai traitement (minutes)',
        }


class TicketFilterForm(forms.Form):
    search = forms.CharField(required=False, label='Recherche',
                             widget=forms.TextInput(attrs={'placeholder': 'Numéro, titre...'}))
    status = forms.MultipleChoiceField(
        required=False, choices=Ticket.STATUS_CHOICES,
        widget=forms.CheckboxSelectMultiple, label='Statut'
    )
    priority = forms.MultipleChoiceField(
        required=False, choices=Ticket.PRIORITY_CHOICES,
        widget=forms.CheckboxSelectMultiple, label='Priorité'
    )
    category = forms.ModelChoiceField(
        required=False, queryset=Category.objects.filter(is_active=True),
        label='Catégorie', empty_label='Toutes'
    )
    application = forms.ModelChoiceField(
        required=False, queryset=Application.objects.filter(is_active=True),
        label='Application', empty_label='Toutes'
    )
    date_from = forms.DateField(required=False, label='Du',
                                widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, label='Au',
                              widget=forms.DateInput(attrs={'type': 'date'}))
    assigned_to_me = forms.BooleanField(required=False, label='Assignés à moi')
    sla_exceeded = forms.BooleanField(required=False, label='SLA dépassé')
    out_of_sla = forms.BooleanField(required=False, label='Résolu hors SLA')
