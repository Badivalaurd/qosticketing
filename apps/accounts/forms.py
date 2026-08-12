from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import User, Department


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Adresse e-mail')
    first_name = forms.CharField(max_length=150, required=True, label='Prénom')
    last_name = forms.CharField(max_length=150, required=True, label='Nom')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].required = True
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.fields['department'].help_text = 'Obligatoire — détermine la visibilité de vos tickets.'
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            'username',
            'email',
            Row(Column('department', css_class='col-md-8'), Column('phone', css_class='col-md-4')),
            Row(Column('password1', css_class='col-md-6'), Column('password2', css_class='col-md-6')),
            Submit('submit', 'Créer le compte', css_class='btn btn-primary w-100 mt-2'),
        )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'bio', 'avatar', 'department']
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'bio': 'Biographie',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True
        self.fields['department'].disabled = True
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            Row(Column('email', css_class='col-md-8'), Column('phone', css_class='col-md-4')),
            Row(Column('department', css_class='col-md-6'), Column('avatar', css_class='col-md-6')),
            'bio',
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'department', 'phone', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].disabled = True
        self.fields['department'].required = True
        self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('username', css_class='col-md-6'), Column('role', css_class='col-md-6')),
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            Row(Column('email', css_class='col-md-8'), Column('phone', css_class='col-md-4')),
            Row(Column('department', css_class='col-md-8'), Column('is_active', css_class='col-md-4')),
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )


class ChooseDepartmentForm(forms.Form):
    """
    Formulaire de choix de département — affiché une seule fois, à la première connexion.
    Exclut tous les départements informatiques (DSI + sous-depts).
    """
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True, is_it_department=False).order_by('name'),
        label='Votre département',
        empty_label='— Sélectionnez votre département —',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.layout = Layout(
            Field('department', css_class='form-select form-select-lg'),
            Submit('submit', 'Confirmer mon département', css_class='btn btn-primary btn-lg w-100 mt-3'),
        )


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'parent', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='btn btn-primary'))
