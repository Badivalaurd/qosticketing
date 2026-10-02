"""
Diagnostic Keycloak — script autonome (sans Django).

Modes :
  python check_keycloak.py          → diagnostic connectivité uniquement
  python check_keycloak.py --login  → saisie interactive identifiant/mot de passe
"""
import getpass
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ── Paramètres (identiques au .env / ConfigMap) ──────────────────────────────
KC_URL    = os.getenv('OIDC_KEYCLOAK_URL',    'http://keycloak.adcm.orangecm/auth')
KC_REALM  = os.getenv('OIDC_KEYCLOAK_REALM',  'digital-app')
CLIENT_ID = os.getenv('OIDC_RP_CLIENT_ID',    'ITTIS')
SECRET    = os.getenv('OIDC_RP_CLIENT_SECRET', '')

DISCOVERY = f"{KC_URL}/realms/{KC_REALM}/.well-known/openid-configuration"
TOKEN_EP  = f"{KC_URL}/realms/{KC_REALM}/protocol/openid-connect/token"

TIMEOUT = 8  # secondes

# ── Couleurs ──────────────────────────────────────────────────────────────────
G  = '\033[32;1m'   # vert   OK
R  = '\033[31;1m'   # rouge  FAIL
Y  = '\033[33;1m'   # jaune  WARN
C  = '\033[36m'     # cyan   info
D  = '\033[90m'     # gris   détail
RS = '\033[0m'

def ok(msg):   print(f"  {G}[OK]{RS}   {msg}")
def fail(msg): print(f"  {R}[FAIL]{RS} {msg}")
def warn(msg): print(f"  {Y}[WARN]{RS} {msg}")
def info(msg): print(f"  {C}[INFO]{RS} {D}{msg}{RS}")


def section(title):
    print(f"\n{C}{'─'*55}{RS}")
    print(f"{C}  {title}{RS}")
    print(f"{C}{'─'*55}{RS}")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_dns(host):
    section(f"1. Résolution DNS — {host}")
    try:
        addrs = socket.getaddrinfo(host, None)
        ips = sorted({a[4][0] for a in addrs})
        ok(f"Résolu → {', '.join(ips)}")
        return ips
    except socket.gaierror as e:
        fail(f"DNS introuvable : {e}")
        return []


def test_tcp(host, port):
    section(f"2. Connexion TCP — {host}:{port}")
    t0 = time.time()
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            ms = int((time.time() - t0) * 1000)
            ok(f"Port {port} ouvert ({ms} ms)")
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        ms = int((time.time() - t0) * 1000)
        fail(f"Port {port} inaccessible après {ms} ms : {e}")
        return False


def test_discovery():
    section(f"3. Endpoint découverte OIDC")
    info(f"GET {DISCOVERY}")
    try:
        import urllib.request
        import json
        req = urllib.request.Request(DISCOVERY, headers={'User-Agent': 'ITTIS-check/1.0'})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ms = int((time.time() - t0) * 1000)
            data = json.loads(r.read())
        ok(f"HTTP {r.status} — réponse en {ms} ms")
        info(f"Issuer  : {data.get('issuer', '?')}")
        info(f"Token   : {data.get('token_endpoint', '?')}")
        info(f"Auth    : {data.get('authorization_endpoint', '?')}")
        return data
    except Exception as e:
        fail(str(e))
        return None


def test_token(discovery_data):
    section(f"4. Authentification client (client_credentials)")
    if not SECRET:
        warn("OIDC_RP_CLIENT_SECRET vide — test ignoré.")
        return
    ep = (discovery_data or {}).get('token_endpoint', TOKEN_EP)
    info(f"POST {ep}")
    info(f"client_id = {CLIENT_ID}")
    try:
        body = urllib.parse.urlencode({
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': SECRET,
        }).encode()
        req = urllib.request.Request(ep, data=body, method='POST',
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ms = int((time.time() - t0) * 1000)
            data = json.loads(r.read())
        ok(f"Token obtenu en {ms} ms (type: {data.get('token_type', '?')})")
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors='replace')
        fail(f"HTTP {e.code} : {body_text[:200]}")
    except Exception as e:
        fail(str(e))


def _http_post(url, payload):
    body = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(
        url, data=body, method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read()), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode(errors='replace') or '{}'), int((time.time() - t0) * 1000)


def _decode_jwt_claims(token):
    """Décode le payload JWT sans vérification de signature (diagnostic uniquement)."""
    import base64
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return {}
        pad = parts[1] + '=' * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(pad))
    except Exception:
        return {}


def mode_login_interactif(discovery_data):
    section("Connexion interactive — saisie identifiant / mot de passe")

    ep = (discovery_data or {}).get('token_endpoint', TOKEN_EP) if discovery_data else TOKEN_EP

    print(f"\n  {D}Les valeurs entre [crochets] sont les valeurs par défaut.{RS}")
    print(f"  {D}Appuyez sur Entrée pour les conserver.{RS}\n")

    # Config modifiable interactivement
    kc_url_i   = input(f"  URL Keycloak    [{KC_URL}] : ").strip() or KC_URL
    realm_i    = input(f"  Realm           [{KC_REALM}] : ").strip() or KC_REALM
    client_i   = input(f"  Client ID       [{CLIENT_ID}] : ").strip() or CLIENT_ID
    secret_i   = getpass.getpass(f"  Client Secret   [***] : ") or SECRET

    ep_i = f"{kc_url_i}/realms/{realm_i}/protocol/openid-connect/token"

    print()
    username = input(f"  Identifiant (CUID ou email) : ").strip()
    password = getpass.getpass(f"  Mot de passe               : ")

    if not username or not password:
        fail("Identifiant et mot de passe obligatoires.")
        return

    section("Tentative de connexion")
    info(f"Token endpoint : {ep_i}")
    info(f"Utilisateur    : {username}")

    status, data, ms = _http_post(ep_i, {
        'grant_type': 'password',
        'client_id':  client_i,
        'client_secret': secret_i,
        'username': username,
        'password': password,
        'scope': 'openid email profile',
    })

    if status == 200 and 'access_token' in data:
        ok(f"Authentification réussie en {ms} ms")
        claims = _decode_jwt_claims(data['access_token'])
        if claims:
            print()
            info(f"Sujet (sub)          : {claims.get('sub', '?')}")
            info(f"Nom préféré          : {claims.get('preferred_username', '?')}")
            info(f"Email                : {claims.get('email', '?')}")
            info(f"Prénom               : {claims.get('given_name', '?')}")
            info(f"Nom                  : {claims.get('family_name', '?')}")
            roles = claims.get('realm_access', {}).get('roles', [])
            info(f"Rôles realm          : {', '.join(roles) or '(aucun)'}")
            exp = claims.get('exp')
            if exp:
                import datetime
                exp_dt = datetime.datetime.fromtimestamp(exp)
                info(f"Token expire à       : {exp_dt.strftime('%H:%M:%S')}")
    elif status == 401:
        fail(f"Identifiants incorrects (HTTP 401)")
        err = data.get('error_description') or data.get('error', '')
        if err:
            info(f"Détail : {err}")
    elif status == 400:
        fail(f"Requête rejetée (HTTP 400)")
        err = data.get('error_description') or data.get('error', '')
        if err:
            warn(f"Détail : {err}")
        warn("Vérifiez que le flux 'Direct Access Grants' est activé sur le client Keycloak.")
    else:
        fail(f"HTTP {status} — {data}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    from urllib.parse import urlparse
    parsed = urlparse(KC_URL)
    host   = parsed.hostname
    port   = parsed.port or (443 if parsed.scheme == 'https' else 80)

    print(f"\n{C}{'═'*55}{RS}")
    print(f"{C}  Diagnostic Keycloak / OIDC — ITTIS{RS}")
    print(f"{C}{'═'*55}{RS}")
    info(f"URL    : {KC_URL}")
    info(f"Realm  : {KC_REALM}")
    info(f"Client : {CLIENT_ID}")

    test_dns(host)
    tcp_ok = test_tcp(host, port)

    # Tester aussi le port 8080 si le port par défaut échoue
    if not tcp_ok and port == 80:
        section(f"2b. Retry TCP — {host}:8080 (port Keycloak par défaut)")
        if test_tcp(host, 8080):
            warn(f"Keycloak répond sur 8080 — mets à jour OIDC_KEYCLOAK_URL avec :{8080}")

    discovery = test_discovery()
    test_token(discovery)

    print(f"\n{C}{'═'*55}{RS}\n")


if __name__ == '__main__':
    if '--login' in sys.argv:
        print(f"\n{C}{'═'*55}{RS}")
        print(f"{C}  Keycloak — Test de connexion interactif — ITTIS{RS}")
        print(f"{C}{'═'*55}{RS}")
        info(f"URL    : {KC_URL}")
        info(f"Realm  : {KC_REALM}")
        from urllib.parse import urlparse
        parsed = urlparse(KC_URL)
        host   = parsed.hostname
        port   = parsed.port or (443 if parsed.scheme == 'https' else 80)
        test_dns(host)
        tcp_ok = test_tcp(host, port)
        if not tcp_ok:
            fail("Keycloak inaccessible — connexion impossible.")
            sys.exit(1)
        discovery = test_discovery()
        mode_login_interactif(discovery)
        print(f"\n{C}{'═'*55}{RS}\n")
    else:
        main()
