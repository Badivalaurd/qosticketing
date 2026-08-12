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
    # Parents first, then children
    parents_data = [
        # (name, code, is_it, is_placeholder)
        ('Département Informatique',              'DSI',    True,  False),
        ('Département Général',                   'DG',     False, False),
        ('Département Administratif et Financier','DAF',    False, False),
        ('Département Commercial',                'DCOM',   False, False),
        ('Département des Ressources Humaines',   'DRH',    False, False),
        ('Département Technique',                 'DT',     False, False),
        ('Département Marketing',                 'DMKT',   False, False),
        ('Sans Département',                      'NO-DEPT',False, True),
    ]
    objs = {}
    for name, code, is_it, is_ph in parents_data:
        d, created = Department.objects.get_or_create(
            code=code, defaults={'name': name, 'is_it_department': is_it, 'is_placeholder': is_ph}
        )
        if not created and is_it and not d.is_it_department:
            d.is_it_department = True
            d.save()
        objs[code] = d
        tag = '[IT]' if d.is_it_department else ('[provisoire]' if d.is_placeholder else '')
        print(f"  {'Créé' if created else 'Existant'}: {d} {tag}")

    # Sous-départements IT (héritent is_it via Department.save())
    children_data = [
        ("Maîtrise d'Ouvrage", 'MOA',   'DSI'),
        ('SI / QoS',           'SIQOS', 'DSI'),
    ]
    for name, code, parent_code in children_data:
        parent = objs.get(parent_code)
        d, created = Department.objects.get_or_create(
            code=code, defaults={'name': name, 'is_it_department': True, 'parent': parent}
        )
        if not created and parent and not d.parent:
            d.parent = parent
            d.save()
        objs[code] = d
        print(f"  {'Créé' if created else 'Existant'}: {d} [IT sous-dept de {parent_code}]")
    return objs


def create_users(depts):
    print("Création des utilisateurs...")
    # Uniquement les 2 comptes génériques — skip si déjà existants
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@omcm.local')
    users = [
        ('admin_omcm', 'Admin', 'OMCM',    admin_email,       'admin@123',  User.ROLE_ADMIN, 'DSI'),
        ('agent_omcm', 'Agent', 'Support', 'agent@omcm.local', 'agent@123',  User.ROLE_AGENT, 'DSI'),
    ]
    for username, first, last, email, pwd, role, dept_code in users:
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


def create_categories(depts):
    print("Création des catégories...")
    moa = depts.get('MOA')
    siqos = depts.get('SIQOS')

    # (type, name, icon, color, it_team)
    cats = [
        (Category.INCIDENT,     'Incident',             'bi-exclamation-triangle', 'danger',  siqos),
        (Category.EVOLUTION,    "Demande d'Évolution",  'bi-lightbulb',            'primary', moa),
        (Category.SUPPORT,      'Support Fonctionnel',  'bi-headset',              'info',    siqos),
        (Category.PONCTUEL,     'Demande Ponctuelle',   'bi-clipboard-check',      'warning', siqos),
        (Category.TACHE_PROJET, 'Tâche Projet',         'bi-kanban',               'success', moa),
    ]
    subs = {
        Category.INCIDENT:     ['Application indisponible', 'Erreur transaction', 'Panne interface', 'Lenteur'],
        Category.EVOLUTION:    ['Nouveau rapport', 'Modification workflow', 'Nouveau champ', 'Interface'],
        Category.SUPPORT:      ['Explication traitement', 'Assistance écran', 'Anomalie métier'],
        Category.PONCTUEL:     ['Extraction données', 'Paramétrage exceptionnel', 'Déblocage'],
        Category.TACHE_PROJET: ['Développement', 'Tests', 'Documentation', 'Déploiement'],
    }
    for type_, name, icon, color, it_team in cats:
        cat, created = Category.objects.get_or_create(type=type_, defaults={
            'name': name, 'icon': icon, 'color': color, 'it_team': it_team
        })
        if not created and it_team and cat.it_team != it_team:
            cat.it_team = it_team
            cat.save(update_fields=['it_team'])
        for sub_name in subs.get(type_, []):
            SubCategory.objects.get_or_create(category=cat, name=sub_name)
    print("  Catégories et sous-catégories créées.")


def create_applications(depts):
    print("Création des applications...")
    dsi = depts.get('DSI')
    apps = [
        ('Tango',                'TANGO',   dsi, 'Core Banking System — traitement des transactions Orange Money'),
        ('Global Reporting',     'GREPORT', dsi, 'Plateforme de reporting proposée aux partenaires'),
        ('Customer Care',        'CC',      dsi, 'Système de gestion de la relation client'),
        ('OMAPI',                'OMAPI',   dsi, 'API Orange Money — intégration partenaires'),
        ('IRT Sortant',          'IRTS',    dsi, 'Système de traitement des paiements sortants'),
        ('IRT Entrant',          'IRTE',    dsi, 'Système de traitement des paiements entrants'),
        ('Eneo Prepaid',         'ENEOPRE', dsi, 'Paiement factures Eneo — électricité prépayée'),
        ('Eneo Postpaid',        'ENEOPOS', dsi, 'Paiement factures Eneo — électricité postpayée'),
        ('CAMWATER',             'CAMW',    dsi, 'Paiement factures CAMWATER — eau'),
        ('Posome',               'POSOME',  dsi, 'Système de collecte et reversement'),
        ('Facturier Générique',  'FACTGEN', dsi, 'Moteur de facturation générique multi-services'),
        ('Autre',                'AUTRE',   dsi, 'Application non listée ou transverse'),
    ]
    for name, code, dept, desc in apps:
        Application.objects.get_or_create(code=code, defaults={'name': name, 'department': dept, 'description': desc})


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
    print("=== Initialisation des données ITTIS ===\n")
    depts = create_departments()
    create_users(depts)
    create_categories(depts)
    create_applications(depts)
    create_sla_configs()
    create_kb_categories()
    print("\n=== Terminé ! ===")
    print("\nComptes génériques:")
    print("  admin_omcm / admin@123  (Administrateur)")
    print("  agent_omcm / agent@123  (Agent de Support)")
    print("  → Modifiez email et mot de passe depuis l'admin Django après le premier login.")
    print("\nURLs:")
    print("  Dashboard    : http://localhost:8000/dashboard/")
    print("  Admin Django : http://localhost:8000/omcm-backoffice/")
    print("  API Docs     : http://localhost:8000/api/docs/")
    print("  SLA Config   : http://localhost:8000/tickets/sla-config/")
