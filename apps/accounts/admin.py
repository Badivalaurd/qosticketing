import io
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from .models import User, Department, AuditLog, AuthorizedEmployee


# ── Admin AuthorizedEmployee ──────────────────────────────────────────────────

@admin.register(AuthorizedEmployee)
class AuthorizedEmployeeAdmin(admin.ModelAdmin):

    list_display   = ['cuid', 'employee_status', 'department', 'is_registered', 'registered_user', 'uploaded_at']
    list_filter    = ['employee_status', 'department', 'is_registered']
    search_fields  = ['cuid']
    readonly_fields = ['is_registered', 'registered_user', 'uploaded_at']
    ordering       = ['cuid']

    fieldsets = [
        (None, {
            'fields': ['cuid', 'employee_status', 'department'],
            'description': 'CUID en majuscules. Le département doit exister dans la base.',
        }),
        ('Inscription', {
            'fields': ['is_registered', 'registered_user', 'uploaded_at'],
            'classes': ['collapse'],
        }),
    ]

    # ── URL custom pour l'upload ──────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload-cuid/',
                self.admin_site.admin_view(self.upload_cuid_view),
                name='accounts_authorizedemployee_upload',
            ),
        ]
        return custom + urls

    # ── Bouton dans la barre d'outils de la liste ─────────────────────────────

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['upload_url'] = reverse('admin:accounts_authorizedemployee_upload')
        return super().changelist_view(request, extra_context=extra_context)

    # ── Vue d'upload ──────────────────────────────────────────────────────────

    def upload_cuid_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            'title': 'Charger des CUIDs autorisés',
            'opts': self.model._meta,
            'results': None,
        }

        if request.method == 'POST':
            f = request.FILES.get('excel_file')
            if not f:
                self.message_user(request, "Aucun fichier sélectionné.", messages.ERROR)
            elif not f.name.endswith(('.xlsx', '.xls', '.csv')):
                self.message_user(request, "Format non supporté. Utilisez .xlsx, .xls ou .csv", messages.ERROR)
            else:
                try:
                    results = _parse_and_import(f)
                    context['results'] = results
                    self.message_user(
                        request,
                        f"{results['created']} créé(s) · {results['updated']} mis à jour · {results['skipped']} ignoré(s).",
                        messages.SUCCESS,
                    )
                except Exception as exc:
                    self.message_user(request, f"Erreur : {exc}", messages.ERROR)

        return render(request, 'admin/accounts/authorizedemployee/upload_cuid.html', context)


# ── Parser Excel/CSV ──────────────────────────────────────────────────────────

STATUS_MAP = {
    'permanent': 'permanent', 'permanente': 'permanent',
    'interimaire': 'interimaire', 'intérimaire': 'interimaire',
    'interim': 'interimaire', 'intérim': 'interimaire',
    'stagiaire': 'stagiaire',
    'temporaire': 'temporaire',
}


def _parse_and_import(file_obj):
    name = file_obj.name.lower()
    if name.endswith('.csv'):
        return _import_csv(file_obj)
    return _import_excel(file_obj)


def _import_excel(file_obj):
    import openpyxl
    wb = openpyxl.load_workbook(filename=io.BytesIO(file_obj.read()), read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    return _import_rows(rows)


def _import_csv(file_obj):
    import csv, codecs
    content = file_obj.read()
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = content.decode('latin-1')
    reader = csv.reader(io.StringIO(text))
    next(reader, None)  # skip header
    rows = [tuple(r) for r in reader]
    return _import_rows(rows)


def _import_rows(rows):
    results = {'created': 0, 'updated': 0, 'skipped': 0, 'rows': []}

    for idx, row in enumerate(rows, start=2):
        if not row or not row[0]:
            results['skipped'] += 1
            continue

        cuid   = str(row[0]).strip().upper()
        statut = str(row[1]).strip().lower() if len(row) > 1 and row[1] else 'permanent'
        dept   = str(row[2]).strip()         if len(row) > 2 and row[2] else ''

        if not cuid:
            results['skipped'] += 1
            continue

        employee_status = STATUS_MAP.get(statut, 'permanent')

        # Toujours mettre à jour le statut
        defaults = {'employee_status': employee_status}

        # Département : on le met à jour uniquement s'il est renseigné dans le fichier
        # → un fichier sans colonne Département ne supprime pas le département existant
        dept_display = '—'
        if dept:
            resolved = (
                Department.objects.filter(name__iexact=dept).first()
                or Department.objects.filter(name__icontains=dept).first()
            )
            if resolved:
                defaults['department'] = resolved
                dept_display = resolved.name
            else:
                dept_display = f'"{dept}" introuvable — département inchangé'

        obj, created = AuthorizedEmployee.objects.update_or_create(
            cuid=cuid,
            defaults=defaults,
        )

        if created:
            results['created'] += 1
            results['rows'].append({'cuid': cuid, 'action': 'Créé', 'dept': dept_display, 'statut': employee_status})
        else:
            results['updated'] += 1
            old_statut = obj.employee_status  # valeur AVANT update (déjà écrasée, mais on a le nouveau)
            results['rows'].append({'cuid': cuid, 'action': 'Mis à jour', 'dept': dept_display, 'statut': employee_status})

    return results


# ── Admin Department ──────────────────────────────────────────────────────────

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'parent', 'is_it_department', 'ticketing_enabled', 'manager', 'is_active']
    list_filter   = ['is_active', 'is_it_department', 'ticketing_enabled']
    search_fields = ['name', 'code']
    fieldsets = [
        (None, {'fields': ['name', 'code', 'description', 'parent', 'is_active']}),
        ('Département Informatique', {'fields': ['is_it_department']}),
        ('Activation Ticketing (autres départements)', {
            'fields': ['ticketing_enabled', 'manager'],
            'description': (
                'Activez uniquement après accord contractuel signé. '
                'Le manager choisi sera responsable de la distribution des tickets dans ce département. '
                'Un seul manager par département. Seul l\'admin peut modifier ces champs.'
            ),
        }),
    ]


# ── Admin User ────────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'email', 'get_full_name', 'role', 'department', 'is_active']
    list_filter   = ['role', 'department', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'department', 'phone', 'avatar', 'bio')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'department', 'phone')}),
    )


# ── Admin AuditLog ────────────────────────────────────────────────────────────

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'model_name', 'object_repr', 'ip_address', 'created_at']
    list_filter   = ['action', 'model_name']
    search_fields = ['user__username', 'object_repr', 'details']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 'details', 'ip_address', 'created_at']
    ordering = ['-created_at']
