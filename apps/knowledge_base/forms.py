from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import Article, KBCategory


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['category', 'type', 'title', 'summary', 'content', 'tags', 'is_published']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 15}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, tag3'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('category', css_class='col-md-6'), Column('type', css_class='col-md-6')),
            'title', 'summary', 'content', 'tags',
            Row(Column('is_published', css_class='col-md-4')),
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )


class ArticleAdminForm(forms.ModelForm):
    """Formulaire étendu pour les admins avec restriction de visibilité."""
    class Meta:
        model = Article
        fields = ['category', 'type', 'title', 'summary', 'content', 'tags',
                  'is_published', 'visibility_restricted', 'visible_to_departments']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 15}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, tag3'}),
            'visible_to_departments': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('category', css_class='col-md-6'), Column('type', css_class='col-md-6')),
            'title', 'summary', 'content', 'tags',
            Row(
                Column('is_published', css_class='col-md-4'),
                Column('visibility_restricted', css_class='col-md-4'),
            ),
            Field('visible_to_departments'),
            Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
        )


class KBCategoryForm(forms.ModelForm):
    class Meta:
        model = KBCategory
        fields = ['name', 'description', 'icon', 'color', 'order']
