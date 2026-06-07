"""
Service de synchronisation hors-ligne → PostgreSQL.

Tourne en arrière-plan (thread daemon) dès le démarrage de l'app.
Cycle toutes les 60 secondes :
  1. Vérifie si PostgreSQL est disponible
  2. Synchronise les PendingTickets vers PG
  3. Met à jour le CachedTicket listing
  4. Vérifie le statut de blocage des utilisateurs connectés
"""
import threading
import time
import logging

logger = logging.getLogger(__name__)

_started = False
_lock = threading.Lock()

SYNC_INTERVAL_SECONDS = 60


def start_sync_scheduler():
    """Démarre le thread de synchronisation (une seule fois)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    thread = threading.Thread(target=_run_loop, name='SyncService', daemon=True)
    thread.start()
    logger.info("SyncService démarré (intervalle %ds)", SYNC_INTERVAL_SECONDS)


def _run_loop():
    # Attendre que Django soit complètement prêt
    time.sleep(5)
    while True:
        try:
            _sync_cycle()
        except Exception as exc:
            logger.exception("Erreur dans le cycle de sync : %s", exc)
        time.sleep(SYNC_INTERVAL_SECONDS)


def _sync_cycle():
    from config.db_availability import is_postgres_available, invalidate_cache
    invalidate_cache()

    if not is_postgres_available():
        logger.debug("PG indisponible — sync ignorée")
        return

    logger.info("PG disponible — début du cycle de sync")
    _sync_pending_tickets()
    _check_blocked_users()
    logger.info("Cycle de sync terminé")


def _sync_pending_tickets():
    """Pousse tous les PendingTickets vers PostgreSQL."""
    from apps.local_sync.models import PendingTicket
    from apps.accounts.models import User, Department
    from apps.tickets.models import Ticket, Category

    pending = PendingTicket.objects.using('pending').filter(
        sync_status=PendingTicket.SYNC_PENDING
    )

    for pt in pending:
        try:
            # Récupérer l'utilisateur depuis PG
            creator = User.objects.get(pk=pt.user_id)
            dept = Department.objects.filter(pk=pt.department_id).first()
            target_dept = Department.objects.filter(pk=pt.target_department_id).first()
            category = None
            if pt.category_id:
                category = Category.objects.filter(pk=pt.category_id).first()

            ticket = Ticket(
                title=pt.title,
                description=pt.description,
                priority=pt.priority,
                created_by=creator,
                department=dept,
                target_department=target_dept,
                category=category,
            )
            ticket.save()

            pt.mark_synced(ticket.number)
            logger.info("Ticket hors-ligne synchronisé : %s → %s", pt.local_id, ticket.number)

        except Exception as exc:
            pt.mark_failed(str(exc))
            logger.warning("Échec sync ticket %s : %s", pt.local_id, exc)


def _check_blocked_users():
    """
    Vérifie le statut des utilisateurs en session locale.
    Si un utilisateur est bloqué côté PG → marque son credential local comme inactif.
    La prochaine requête HTTP sera redirigée vers la page de connexion.
    """
    from apps.local_auth.models import LocalCredential
    from apps.accounts.models import User

    local_creds = LocalCredential.objects.using('auth_local').filter(is_active=True)
    for cred in local_creds:
        try:
            pg_user = User.objects.get(pk=cred.pg_user_id)
            if not pg_user.is_active:
                cred.is_active = False
                cred.save(using='auth_local')
                _cancel_pending_for_user(cred.pg_user_id)
                logger.warning("Utilisateur bloqué : %s — credentials locaux invalidés", cred.username)
        except User.DoesNotExist:
            # Compte supprimé côté PG
            cred.is_active = False
            cred.save(using='auth_local')


def _cancel_pending_for_user(user_id: int):
    """Annule tous les tickets hors-ligne d'un utilisateur bloqué."""
    from apps.local_sync.models import PendingTicket
    PendingTicket.objects.using('pending').filter(
        user_id=user_id,
        sync_status=PendingTicket.SYNC_PENDING
    ).update(sync_status=PendingTicket.SYNC_CANCELLED)
