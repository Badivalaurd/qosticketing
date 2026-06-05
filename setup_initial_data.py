"""
Script de configuration initiale.
Exécuter après 'python manage.py migrate' :
    python setup_initial_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User, Department
from apps.tickets.models import Category, SubCategory, Application, SLAConfig
from apps.knowledge_base.models import KBCategory


def create_departments():
    print("Création des départements...")
    depts_data = [
        ('Département Informatique', 'DSI', True),
        ('Direction Générale', 'DG', False),
        ('Direction Financière', 'DAF', False),
        ('Direction Commerciale', 'DCOM', False),
        ('Direction des Ressources Humaines', 'DRH', False),
        ('Direction Technique', 'DT', False),
        ('Direction Marketing', 'DMKT', False),
    ]
    objs = {}
    for name, code, is_it in depts_data:
        d, created = Department.objects.get_or_create(
            code=code, defaults={'name': name, 'is_it_department': is_it}
        )
        if not created and is_it and not d.is_it_department:
            d.is_it_department = True
            d.save()
        objs[code] = d
        print(f"  {'Créé' if created else 'Existant'}: {d} {'[IT]' if d.is_it_department else ''}")
    return objs


def create_users(depts):
    print("Création des utilisateurs...")
    users_data = [
        ('admin',        'Admin',   'Système',    'admin@qos.local',        'admin@123',    User.ROLE_ADMIN,       'DSI'),
        ('manager_dsi',  'Jean',    'Kouassi',    'jkouassi@qos.local',     'password123',  User.ROLE_MANAGER,     'DSI'),
        ('manager_daf',  'Fatou',   'Coulibaly',  'fcoulibaly@qos.local',   'password123',  User.ROLE_MANAGER,     'DAF'),
        ('agent_01',     'Marie',   'Bamba',      'mbamba@qos.local',       'password123',  User.ROLE_AGENT,       'DSI'),
        ('tech_01',      'Pierre',  'Traoré',     'ptraore@qos.local',      'password123',  User.ROLE_TECHNICIEN,  'DSI'),
        ('tech_02',      'Awa',     'Diomandé',   'adiomande@qos.local',    'password123',  User.ROLE_TECHNICIEN,  'DSI'),
        ('demandeur_01', 'Alice',   "N'Guessan",  'anguessan@qos.local',    'password123',  User.ROLE_DEMANDEUR,   'DCOM'),
        ('demandeur_02', 'Robert',  'Diallo',     'rdiallo@qos.local',      'password123',  User.ROLE_DEMANDEUR,   'DAF'),
        ('obs_01',       'Soro',    'Bintou',     'sbintou@qos.local',      'password123',  User.ROLE_OBSERVATEUR, 'DSI'),
    ]
    for username, first, last, email, pwd, role, dept_code in users_data:
        if not User.objects.filter(username=username).exists():
            u = User.objects.create_user(
                username=username, first_name=first, last_name=last,
                email=email, password=pwd, role=role,
                department=depts.get(dept_code),
                is_staff=(role == User.ROLE_ADMIN),
                is_superuser=(role == User.ROLE_ADMIN),
            )
            print(f"  Créé: {u}")
        else:
            print(f"  Existant: {username}")


def create_categories():
    print("Création des catégories...")
    cats = [
        (Category.INCIDENT,     'Incident',             'bi-exclamation-triangle', 'danger'),
        (Category.EVOLUTION,    "Demande d'Évolution",  'bi-lightbulb',            'primary'),
        (Category.SUPPORT,      'Support Fonctionnel',  'bi-headset',              'info'),
        (Category.PONCTUEL,     'Demande Ponctuelle',   'bi-clipboard-check',      'warning'),
        (Category.TACHE_PROJET, 'Tâche Projet',         'bi-kanban',               'success'),
    ]
    subs = {
        Category.INCIDENT:     ['Application indisponible', 'Erreur transaction', 'Panne interface', 'Lenteur'],
        Category.EVOLUTION:    ['Nouveau rapport', 'Modification workflow', 'Nouveau champ', 'Interface'],
        Category.SUPPORT:      ['Explication traitement', 'Assistance écran', 'Anomalie métier'],
        Category.PONCTUEL:     ['Extraction données', 'Paramétrage exceptionnel', 'Déblocage'],
        Category.TACHE_PROJET: ['Développement', 'Tests', 'Documentation', 'Déploiement'],
    }
    for type_, name, icon, color in cats:
        cat, _ = Category.objects.get_or_create(type=type_, defaults={
            'name': name, 'icon': icon, 'color': color
        })
        for sub_name in subs.get(type_, []):
            SubCategory.objects.get_or_create(category=cat, name=sub_name)
    print("  Catégories et sous-catégories créées.")


def create_applications(depts):
    print("Création des applications...")
    apps = [
        ('Core Banking System', 'CBS',    depts.get('DSI')),
        ('ERP Finance',         'ERP',    depts.get('DAF')),
        ('CRM Commercial',      'CRM',    depts.get('DCOM')),
        ('SIRH',                'SIRH',   depts.get('DRH')),
        ('Portail Client',      'PORTAL', depts.get('DCOM')),
        ('Reporting BI',        'BI',     depts.get('DSI')),
    ]
    for name, code, dept in apps:
        Application.objects.get_or_create(code=code, defaults={'name': name, 'department': dept})


def create_sla_configs():
    print("Création des configurations SLA...")
    configs = [
        (SLAConfig.P0, 10,  120),   # P0: 10min prise en charge, 2h traitement
        (SLAConfig.P1, 30,  240),   # P1: 30min, 4h
        (SLAConfig.P2, 120, 1440),  # P2: 2h, 24h
        (SLAConfig.P3, 240, 2880),  # P3: 4h, 48h
    ]
    for priority, response, resolution in configs:
        obj, created = SLAConfig.objects.get_or_create(priority=priority, defaults={
            'response_time_minutes': response,
            'resolution_time_minutes': resolution,
        })
        print(f"  {'Créé' if created else 'Existant'}: {obj}")


def create_kb_categories():
    print("Création des catégories KB...")
    cats = [
        ('FAQ',                  'bi-question-circle', 'info',    1),
        ('Procédures',           'bi-list-check',      'success', 2),
        ('Guides utilisateur',   'bi-book',            'primary', 3),
        ('Solutions récurrentes','bi-lightbulb',       'warning', 4),
    ]
    for name, icon, color, order in cats:
        KBCategory.objects.get_or_create(name=name, defaults={'icon': icon, 'color': color, 'order': order})


if __name__ == '__main__':
    print("=== Initialisation des données QoS Ticketing ===\n")
    depts = create_departments()
    create_users(depts)
    create_categories()
    create_applications(depts)
    create_sla_configs()
    create_kb_categories()
    print("\n=== Terminé ! ===")
    print("\nComptes créés:")
    print("  admin / admin@123              (Administrateur)")
    print("  manager_dsi / password123      (Manager — DSI)")
    print("  manager_daf / password123      (Manager — DAF)")
    print("  agent_01 / password123         (Agent de Support)")
    print("  tech_01 / password123          (Technicien)")
    print("  demandeur_01 / password123     (Demandeur — DCOM)")
    print("\nURLs:")
    print("  Dashboard : http://localhost:8000/dashboard/")
    print("  Admin     : http://localhost:8000/admin/")
    print("  API Docs  : http://localhost:8000/api/docs/")
    print("  SLA Config: http://localhost:8000/tickets/sla-config/")
