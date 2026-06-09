"""
Gestionnaire de logs journaliers par utilisateur.

Structure créée :
  logs/
    2026-06-07.log          ← journal global du jour (tous événements)
    users/
      VFYX5401/
        2026-06-07.log      ← journal du jour pour cet utilisateur
      system/
        2026-06-07.log      ← événements sans utilisateur identifié
"""
import logging
import os
import threading
from datetime import date


class DailyFileHandler(logging.Handler):
    """Journal global journalier : logs/YYYY-MM-DD.log"""

    def __init__(self, log_dir):
        super().__init__()
        self.log_dir = str(log_dir)
        self._current_date = None
        self._file = None
        self._lock = threading.Lock()

    def _open_file(self, today):
        os.makedirs(self.log_dir, exist_ok=True)
        filepath = os.path.join(self.log_dir, f'{today}.log')
        return open(filepath, 'a', encoding='utf-8')

    def emit(self, record):
        with self._lock:
            try:
                today = date.today().strftime('%Y-%m-%d')
                if today != self._current_date:
                    if self._file:
                        self._file.close()
                    self._file = self._open_file(today)
                    self._current_date = today
                self._file.write(self.format(record) + '\n')
                self._file.flush()
            except Exception:
                self.handleError(record)

    def close(self):
        with self._lock:
            if self._file:
                self._file.close()
                self._file = None
        super().close()


class UserDailyFileHandler(logging.Handler):
    """Journal journalier par utilisateur : logs/users/CUID/YYYY-MM-DD.log

    Utilisation dans les vues :
        logger.info("Message", extra={'user': request.user.username})
    Si 'user' absent → écrit dans logs/users/system/YYYY-MM-DD.log
    """

    def __init__(self, log_dir):
        super().__init__()
        self.user_log_dir = os.path.join(str(log_dir), 'users')
        self._locks = {}
        self._files = {}
        self._dates = {}
        self._meta_lock = threading.Lock()

    def _get_lock(self, key):
        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def _sanitize(self, name):
        return ''.join(c for c in str(name) if c.isalnum() or c in ('_', '-', '.')) or 'system'

    def emit(self, record):
        raw_user = getattr(record, 'user', None) or 'system'
        username = self._sanitize(raw_user)
        lock = self._get_lock(username)

        with lock:
            try:
                today = date.today().strftime('%Y-%m-%d')
                if self._dates.get(username) != today:
                    if username in self._files and self._files[username]:
                        self._files[username].close()
                    user_dir = os.path.join(self.user_log_dir, username)
                    os.makedirs(user_dir, exist_ok=True)
                    self._files[username] = open(
                        os.path.join(user_dir, f'{today}.log'), 'a', encoding='utf-8'
                    )
                    self._dates[username] = today
                self._files[username].write(self.format(record) + '\n')
                self._files[username].flush()
            except Exception:
                self.handleError(record)

    def close(self):
        with self._meta_lock:
            for f in self._files.values():
                try:
                    f.close()
                except Exception:
                    pass
            self._files.clear()
        super().close()
