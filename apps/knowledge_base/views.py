from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import KBCategory, Article
from .forms import ArticleForm, ArticleAdminForm


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'knowledge_base/article_list.html'
    context_object_name = 'articles'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user

        # Construire le filtre de visibilité avec Q objects (évite le combine unique/non-unique)
        if user.role == 'ADMIN':
            visibility_filter = Q()  # Tout voir
        elif user.department:
            visibility_filter = (
                Q(is_published=True, visibility_restricted=False) |
                Q(is_published=True, visibility_restricted=True, visible_to_departments=user.department) |
                Q(is_published=False, author=user)
            )
        else:
            visibility_filter = (
                Q(is_published=True, visibility_restricted=False) |
                Q(is_published=False, author=user)
            )

        qs = Article.objects.filter(visibility_filter).distinct().select_related('category', 'author')

        q = self.request.GET.get('q')
        cat = self.request.GET.get('category')
        type_ = self.request.GET.get('type')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__icontains=q))
        if cat:
            qs = qs.filter(category_id=cat)
        if type_:
            qs = qs.filter(type=type_)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = KBCategory.objects.all()
        ctx['types'] = Article.TYPE_CHOICES
        return ctx


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = 'knowledge_base/article_detail.html'

    def get_object(self):
        obj = super().get_object()
        if not obj.can_user_see(self.request.user):
            raise PermissionDenied
        Article.objects.filter(pk=obj.pk).update(views=obj.views + 1)
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_edit'] = self.object.can_user_edit(self.request.user)
        ctx['can_delete'] = self.object.can_user_delete(self.request.user)
        return ctx


@login_required
def article_create(request):
    if request.method == 'POST':
        FormClass = ArticleAdminForm if request.user.role == 'ADMIN' else ArticleForm
        form = FormClass(user=request.user, data=request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            if hasattr(form, 'save_m2m'):
                form.save_m2m()
            messages.success(request, 'Article créé avec succès.')
            return redirect('knowledge_base:detail', pk=article.pk)
    else:
        FormClass = ArticleAdminForm if request.user.role == 'ADMIN' else ArticleForm
        form = FormClass(user=request.user)
    return render(request, 'knowledge_base/article_form.html', {'form': form})


@login_required
def article_update(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if not article.can_user_edit(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        FormClass = ArticleAdminForm if request.user.role == 'ADMIN' else ArticleForm
        form = FormClass(user=request.user, data=request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article mis à jour.')
            return redirect('knowledge_base:detail', pk=pk)
    else:
        FormClass = ArticleAdminForm if request.user.role == 'ADMIN' else ArticleForm
        form = FormClass(user=request.user, instance=article)
    return render(request, 'knowledge_base/article_form.html', {'form': form, 'article': article})


@login_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if not article.can_user_delete(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article supprimé.')
        return redirect('knowledge_base:list')
    return render(request, 'knowledge_base/article_confirm_delete.html', {'article': article})
