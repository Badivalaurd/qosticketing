"""
Routeur multi-base de données.

Stratégie :
  - local_auth  → base SQLite `auth_local`  (credentials locaux)
  - local_sync  → base SQLite `pending` (tickets hors-ligne)
                  ou `cache`   (listing offline)
  - updater     → base PostgreSQL `default`
  - tout le reste → `default` (PostgreSQL) quand disponible

Les migrations de chaque app sont restreintes à leur base propre.
"""


class DesktopDBRouter:
    # Mapping app_label → alias de base
    SQLITE_ROUTING = {
        'local_auth': 'auth_local',
        'local_sync': 'local_sync',   # géré plus finement ci-dessous
    }

    POSTGRES_ONLY = {
        'updater', 'accounts', 'tickets', 'projects',
        'notifications', 'knowledge_base', 'dashboard',
        'reporting', 'api',
        # django internals
        'admin', 'auth', 'contenttypes', 'sessions',
    }

    def db_for_read(self, model, **hints):
        label = model._meta.app_label
        if label == 'local_auth':
            return 'auth_local'
        if label == 'local_sync':
            return self._sync_db(model)
        return 'default'

    def db_for_write(self, model, **hints):
        label = model._meta.app_label
        if label == 'local_auth':
            return 'auth_local'
        if label == 'local_sync':
            return self._sync_db(model)
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Relations autorisées dans la même "zone" de BD
        db1 = self._db_for_object(obj1)
        db2 = self._db_for_object(obj2)
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'local_auth':
            return db == 'auth_local'
        if app_label == 'local_sync':
            return db in ('pending', 'cache')
        # Tout le reste → PostgreSQL uniquement
        return db == 'default'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _sync_db(self, model):
        name = model.__name__.lower()
        if 'pending' in name:
            return 'pending'
        if 'cached' in name:
            return 'cache'
        return 'pending'

    def _db_for_object(self, obj):
        label = obj._meta.app_label
        if label == 'local_auth':
            return 'auth_local'
        if label == 'local_sync':
            return self._sync_db(type(obj))
        return 'default'
