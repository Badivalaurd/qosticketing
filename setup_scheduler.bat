@echo off
:: ============================================================
:: QoS Ticketing — Configuration du Planificateur de tâches Windows
:: Lance automatiquement les alertes SLA et le digest quotidien
:: Exécuter UNE SEULE FOIS en tant qu'Administrateur
:: ============================================================

SET PROJECT_DIR=%~dp0
SET PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe
SET MANAGE=%PROJECT_DIR%manage.py

echo.
echo [QoS Ticketing] Configuration des tâches planifiées...
echo.

:: --- Tâche 1 : Vérification SLA toutes les minutes ---
schtasks /Create /F /SC MINUTE /MO 1 ^
  /TN "QoS_Ticketing\check_sla_warnings" ^
  /TR "\"%PYTHON%\" \"%MANAGE%\" check_sla_warnings" ^
  /ST 00:00 ^
  /RL HIGHEST
echo [OK] Tâche check_sla_warnings créée (toutes les minutes)

:: --- Tâche 2 : Digest SLA quotidien à 8h00 ---
schtasks /Create /F /SC DAILY ^
  /TN "QoS_Ticketing\send_daily_digest" ^
  /TR "\"%PYTHON%\" \"%MANAGE%\" send_daily_digest" ^
  /ST 08:00 ^
  /RL HIGHEST
echo [OK] Tâche send_daily_digest créée (tous les jours à 08:00)

echo.
echo ============================================================
echo Tâches planifiées configurées avec succès !
echo Pour vérifier : Planificateur de tâches > QoS_Ticketing
echo Pour supprimer : schtasks /Delete /TN "QoS_Ticketing\check_sla_warnings" /F
echo ============================================================
pause
