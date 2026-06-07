"""
QoS Ticketing — Launcher Windows (exécutable autonome)

Point d'entrée compilé par PyInstaller → QoSTicketing.exe

Responsabilités :
  1. Auto-installation (copie dans %APPDATA%\QoSTicketing\app\ si première exécution)
  2. Vérification de version / mise à jour forcée
  3. Démarrage du serveur Django local sur localhost:port libre
  4. Ouverture du navigateur par défaut
  5. Maintien de l'application ouverte jusqu'à fermeture du navigateur
"""

import os
import sys
import socket
import threading
import time
import webbrowser
import shutil
import subprocess
import logging
from pathlib import Path

# ── Constantes ──────────────────────────────────────────────────────────────
APP_NAME = "QoSTicketing"
APP_VERSION = "1.1.0"
APP_EXE_NAME = "QoSTicketing.exe"

# ── Chemins ──────────────────────────────────────────────────────────────────

def get_appdata_root() -> Path:
    appdata = os.environ.get('APPDATA', '')
    if not appdata:
        appdata = Path.home() / 'AppData' / 'Roaming'
    return Path(appdata) / APP_NAME


def get_data_dir() -> Path:
    return get_appdata_root() / 'data'


def get_install_dir() -> Path:
    return get_appdata_root() / 'app'


def get_installed_exe() -> Path:
    return get_install_dir() / APP_EXE_NAME


def is_running_from_install_dir() -> bool:
    if not getattr(sys, 'frozen', False):
        return True  # Mode dev — pas de gestion d'installation
    current = Path(sys.executable).resolve()
    installed = get_installed_exe().resolve()
    return current == installed


# ── Installation / Mise à jour ───────────────────────────────────────────────

def install_if_needed():
    """
    Si l'exe est lancé depuis un autre emplacement (ex: Téléchargements),
    il se copie dans le répertoire d'installation et se relance.
    Cela garantit que la mise à jour écrase toujours le même fichier.
    """
    if not getattr(sys, 'frozen', False):
        return

    if is_running_from_install_dir():
        return

    install_dir = get_install_dir()
    install_dir.mkdir(parents=True, exist_ok=True)

    target = get_installed_exe()
    current = Path(sys.executable)

    # Copier l'exe (l'ancien sera écrasé)
    shutil.copy2(str(current), str(target))

    # Créer un raccourci Bureau (via PowerShell)
    _create_desktop_shortcut(target)

    # Relancer depuis le bon emplacement
    subprocess.Popen([str(target)] + sys.argv[1:])
    sys.exit(0)


def _create_desktop_shortcut(target_exe: Path):
    """Crée un raccourci Bureau via PowerShell (Windows uniquement)."""
    try:
        desktop = Path.home() / 'Desktop'
        shortcut = desktop / f"{APP_NAME}.lnk"
        ps_script = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$sc = $ws.CreateShortcut("{shortcut}"); '
            f'$sc.TargetPath = "{target_exe}"; '
            f'$sc.WorkingDirectory = "{target_exe.parent}"; '
            f'$sc.Description = "QoS Ticketing"; '
            f'$sc.Save()'
        )
        subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_script],
            capture_output=True
        )
    except Exception:
        pass


# ── Port libre ────────────────────────────────────────────────────────────────

def find_free_port(preferred: int = 8765) -> int:
    # Essayer le port préféré d'abord (pour des raisons de cache navigateur)
    for port in [preferred] + list(range(preferred + 1, preferred + 100)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError("Aucun port libre disponible.")


# ── Démarrage Django ──────────────────────────────────────────────────────────

def configure_django(port: int, data_dir: Path):
    """Configure les variables d'environnement avant l'import de Django."""
    # Lire la config réseau depuis le fichier .env de données (modifiable sans recompiler)
    env_file = data_dir / 'network.env'
    if env_file.exists():
        _load_env_file(env_file)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_desktop')
    os.environ['QOS_DATA_DIR'] = str(data_dir)
    os.environ['QOS_PORT'] = str(port)
    os.environ['QOS_VERSION'] = APP_VERSION

    # Ajouter le répertoire de l'exe (ou du projet en mode dev) au path Python
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)  # Répertoire temporaire PyInstaller
    else:
        base = Path(__file__).parent

    if str(base) not in sys.path:
        sys.path.insert(0, str(base))


def _load_env_file(path: Path):
    """Charge un fichier KEY=VALUE dans os.environ."""
    try:
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                os.environ.setdefault(key.strip(), value.strip())
    except Exception:
        pass


def run_django_server(port: int):
    """Lance le serveur WSGI Django (bloquant)."""
    import django
    django.setup()

    # Migrations des bases SQLite locales
    from django.core.management import call_command
    for db in ['auth_local', 'pending', 'cache']:
        try:
            call_command('migrate', '--database', db, '--run-syncdb', verbosity=0)
        except Exception as exc:
            logging.warning("Migration %s : %s", db, exc)

    # Serveur WSGI minimal (pas besoin de Gunicorn en local)
    from django.core.wsgi import get_wsgi_application
    from wsgiref.simple_server import make_server, WSGIRequestHandler

    class QuietHandler(WSGIRequestHandler):
        def log_message(self, fmt, *args):
            pass  # Silencieux — logs dans le fichier de données

    application = get_wsgi_application()
    httpd = make_server('127.0.0.1', port, application, handler_class=QuietHandler)
    httpd.serve_forever()


# ── Attente du serveur ────────────────────────────────────────────────────────

def wait_for_server(port: int, timeout_sec: int = 20) -> bool:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            with socket.socket() as s:
                s.settimeout(1)
                s.connect(('127.0.0.1', port))
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.25)
    return False


# ── UI d'erreur (Tkinter) ─────────────────────────────────────────────────────

def show_error(title: str, message: str):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        pass  # Si Tkinter absent, on ignore


def show_update_required(version: str, download_url: str, notes: str):
    try:
        import tkinter as tk
        from tkinter import ttk
        import webbrowser as wb

        root = tk.Tk()
        root.title(f"Mise à jour requise — {APP_NAME}")
        root.geometry("500x320")
        root.resizable(False, False)

        ttk.Label(root, text="⚠  Mise à jour requise", font=("Segoe UI", 14, "bold")).pack(pady=20)
        ttk.Label(root, text=f"Nouvelle version disponible : v{version}", font=("Segoe UI", 11)).pack()
        ttk.Label(root, text="Vous devez mettre à jour l'application pour continuer.", font=("Segoe UI", 10)).pack(pady=5)

        if notes:
            frame = ttk.LabelFrame(root, text="Notes de version", padding=10)
            frame.pack(fill="x", padx=20, pady=10)
            ttk.Label(frame, text=notes[:300], wraplength=440, justify="left").pack()

        def open_download():
            wb.open(download_url)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Télécharger la mise à jour", command=open_download).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Quitter", command=root.destroy).pack(side="left", padx=5)

        root.mainloop()
    except Exception:
        show_error("Mise à jour requise",
                   f"Nouvelle version v{version} disponible.\nTéléchargez-la ici : {download_url}")


# ── Point d'entrée ────────────────────────────────────────────────────────────

def main():
    # 1. Installation si nécessaire (copie dans AppData)
    install_if_needed()

    # 2. Répertoire de données
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    # 3. Port libre
    port = find_free_port()

    # 4. Configurer Django
    configure_django(port, data_dir)

    # 5. Vérification de mise à jour (avant de lancer le serveur)
    try:
        from apps.updater.version_check import check_update_required
        status = check_update_required(APP_VERSION)
        if status.get('update_required'):
            show_update_required(
                version=status['latest_version'],
                download_url=status['download_url'],
                notes=status.get('release_notes', ''),
            )
            sys.exit(0)
    except Exception:
        pass  # PG indisponible au démarrage → on laisse passer

    # 6. Lancer Django en arrière-plan
    server_thread = threading.Thread(
        target=run_django_server,
        args=(port,),
        name='DjangoServer',
        daemon=True,
    )
    server_thread.start()

    # 7. Attendre que le serveur soit prêt
    if not wait_for_server(port):
        show_error("QoS Ticketing",
                   "Le serveur n'a pas démarré dans les délais.\n"
                   "Vérifiez les logs dans le dossier de données.")
        sys.exit(1)

    # 8. Ouvrir le navigateur
    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)

    # 9. Maintenir l'application active
    try:
        server_thread.join()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
