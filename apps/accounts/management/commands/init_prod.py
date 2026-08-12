"""
Commande d'initialisation minimale pour la production.
Crée uniquement ce qui est indispensable au démarrage de l'application.

Usage :
    python manage.py init_prod
    python manage.py init_prod --no-demo    (sans les catégories/SLA démo)
"""
import os

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Initialise les données essentielles (admin, agent, DSI, catégories, SLA)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-demo', action='store_true',
            help="Ne crée pas les catégories et SLA par défaut."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== init_prod ==="))
        self._create_depts()
        self._create_users()
        self._create_applications()
        if not options['no_demo']:
            self._create_categories()
            self._create_sla()
        self.stdout.write(self.style.SUCCESS("\nPrêt. Connectez-vous avec :"))
        self.stdout.write("  URL     : /dashboard/")
        self.stdout.write("  Admin   : admin_omcm  /  admin@123")
        self.stdout.write("  Agent   : agent_omcm  /  agent@123")
        self.stdout.write("  Backoffice Django : /omcm-backoffice/")
        self.stdout.write("  Modifiez email et mot de passe depuis l'admin apres le premier login.")

    # ── Départements ──────────────────────────────────────────────────────────
    def _create_depts(self):
        from apps.accounts.models import Department
        depts_data = [
            # (name, code, is_it, is_placeholder, parent_code)
            ('Département Informatique',              'DSI',    True,  False, None),
            ('Département Général',                   'DG',     False, False, None),
            ('Département Administratif et Financier','DAF',    False, False, None),
            ('Département Commercial',                'DCOM',   False, False, None),
            ('Département des Ressources Humaines',   'DRH',    False, False, None),
            ('Département Technique',                 'DT',     False, False, None),
            ('Département Marketing',                 'DMKT',   False, False, None),
            ('Sans Département',                      'NO-DEPT',False, True,  None),
            # Sous-départements IT (parent=DSI — héritent is_it via Department.save())
            ('Maîtrise d\'Ouvrage',                  'MOA',    True,  False, 'DSI'),
            ('SI / QoS',                             'SIQOS',  True,  False, 'DSI'),
        ]
        created_depts = {}
        # Créer les parents en premier
        for name, code, is_it, is_ph, parent_code in depts_data:
            if parent_code is not None:
                continue
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={'name': name, 'is_it_department': is_it, 'is_placeholder': is_ph},
            )
            if is_it and not dept.is_it_department:
                dept.is_it_department = True
                dept.save()
            created_depts[code] = dept
            status = "Créé" if created else "Existant"
            self.stdout.write(f"  Département : {status} — {dept.name}")
        # Puis les sous-départements
        for name, code, is_it, is_ph, parent_code in depts_data:
            if parent_code is None:
                continue
            parent = created_depts.get(parent_code)
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'is_it_department': is_it,
                    'is_placeholder': is_ph, 'parent': parent
                },
            )
            if parent and not dept.parent:
                dept.parent = parent
                dept.save()
            created_depts[code] = dept
            status = "Créé" if created else "Existant"
            self.stdout.write(f"  Sous-dept   : {status} — {dept.name} (parent: {parent_code})")

    # ── Applications ──────────────────────────────────────────────────────────
    def _create_applications(self):
        from apps.tickets.models import Application
        from apps.accounts.models import Department
        try:
            dsi = Department.objects.get(code='DSI')
        except Department.DoesNotExist:
            self.stdout.write(self.style.WARNING("  Applications : DSI introuvable, ignoré."))
            return
        apps = [
            ('Tango',               'TANGO',   'Core Banking System — traitement des transactions Orange Money'),
            ('Global Reporting',    'GREPORT', 'Plateforme de reporting proposée aux partenaires'),
            ('Customer Care',       'CC',      'Système de gestion de la relation client'),
            ('OMAPI',               'OMAPI',   'API Orange Money — intégration partenaires'),
            ('IRT Sortant',         'IRTS',    'Système de traitement des paiements sortants'),
            ('IRT Entrant',         'IRTE',    'Système de traitement des paiements entrants'),
            ('Eneo Prepaid',        'ENEOPRE', 'Paiement factures Eneo — électricité prépayée'),
            ('Eneo Postpaid',       'ENEOPOS', 'Paiement factures Eneo — électricité postpayée'),
            ('CAMWATER',            'CAMW',    'Paiement factures CAMWATER — eau'),
            ('Posome',              'POSOME',  'Système de collecte et reversement'),
            ('Facturier Générique', 'FACTGEN', 'Moteur de facturation générique multi-services'),
            ('Autre',               'AUTRE',   'Application non listée ou transverse'),
        ]
        for name, code, desc in apps:
            Application.objects.get_or_create(
                code=code,
                defaults={'name': name, 'department': dsi, 'description': desc},
            )
        self.stdout.write("  Applications : OK")

    # ── Comptes essentiels ────────────────────────────────────────────────────
    def _create_users(self):
        from apps.accounts.models import User, Department
        dsi = Department.objects.get(code='DSI')
        users = [
            dict(username='admin_omcm', first_name='Admin', last_name='OMCM',
                 email=os.getenv('ADMIN_EMAIL', 'admin@omcm.local'), password='admin@123',
                 role=User.ROLE_ADMIN, is_staff=True, is_superuser=True),
            dict(username='agent_omcm', first_name='Agent', last_name='Support',
                 email='agent@omcm.local', password='agent@123',
                 role=User.ROLE_AGENT, is_staff=False, is_superuser=False),
        ]
        for u in users:
            pwd = u.pop('password')
            if not User.objects.filter(username=u['username']).exists():
                User.objects.create_user(**u, department=dsi, password=pwd)
                self.stdout.write(f"  Utilisateur : Créé — {u['username']} ({u['role']})")
            else:
                self.stdout.write(f"  Utilisateur : Existant — {u['username']}")

    # ── Catégories tickets ────────────────────────────────────────────────────
    def _create_categories(self):
        from apps.accounts.models import Department
        from apps.tickets.models import Category, SubCategory

        try:
            moa = Department.objects.get(code='MOA')
        except Department.DoesNotExist:
            moa = None
        try:
            siqos = Department.objects.get(code='SIQOS')
        except Department.DoesNotExist:
            siqos = None

        # (type, name, icon, color, it_team)
        cats = [
            (Category.INCIDENT,     'Incident',            'bi-exclamation-triangle', 'danger',  siqos),
            (Category.EVOLUTION,    "Demande d'Évolution", 'bi-lightbulb',            'primary', moa),
            (Category.SUPPORT,      'Support Fonctionnel', 'bi-headset',              'info',    siqos),
            (Category.PONCTUEL,     'Demande Ponctuelle',  'bi-clipboard-check',      'warning', siqos),
            (Category.TACHE_PROJET, 'Tâche Projet',        'bi-kanban',               'success', moa),
        ]
        subs = {
            Category.INCIDENT:     ['Application indisponible', 'Erreur transaction', 'Panne interface', 'Lenteur'],
            Category.EVOLUTION:    ['Nouveau rapport', 'Modification workflow', 'Nouveau champ'],
            Category.SUPPORT:      ['Explication traitement', 'Assistance écran', 'Anomalie métier'],
            Category.PONCTUEL:     ['Extraction données', 'Paramétrage exceptionnel', 'Déblocage'],
            Category.TACHE_PROJET: ['Développement', 'Tests', 'Documentation', 'Déploiement'],
        }
        for type_, name, icon, color, it_team in cats:
            cat, created = Category.objects.get_or_create(
                type=type_, defaults={'name': name, 'icon': icon, 'color': color, 'it_team': it_team}
            )
            if not created and it_team and cat.it_team != it_team:
                cat.it_team = it_team
                cat.save(update_fields=['it_team'])
            for sub in subs.get(type_, []):
                SubCategory.objects.get_or_create(category=cat, name=sub)
        self.stdout.write("  Catégories  : OK")

    # ── Configs SLA ───────────────────────────────────────────────────────────
    def _create_sla(self):
        from apps.tickets.models import SLAConfig
        configs = [
            (SLAConfig.P0, 10,  120),
            (SLAConfig.P1, 30,  240),
            (SLAConfig.P2, 120, 1440),
            (SLAConfig.P3, 240, 2880),
        ]
        for priority, response, resolution in configs:
            SLAConfig.objects.get_or_create(
                priority=priority,
                defaults={'response_time_minutes': response, 'resolution_time_minutes': resolution},
            )
        self.stdout.write("  SLA         : OK")
