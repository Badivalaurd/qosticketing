@echo off
echo ==============================
echo   QoS Ticketing - Demarrage
echo ==============================

:: Create virtual environment if not exists
if not exist ".venv" (
    echo Creation de l'environnement virtuel...
    python -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate

:: Install dependencies
echo Installation des dependances...
pip install -r requirements.txt --quiet

:: Copy .env if not exists
if not exist ".env" (
    copy .env.example .env
    echo Fichier .env cree. Veuillez le configurer si necessaire.
)

:: Generate and apply migrations
echo Generation des migrations...
python manage.py makemigrations accounts tickets projects notifications knowledge_base
echo Application des migrations...
python manage.py migrate

:: Load initial data
echo Chargement des donnees initiales...
python setup_initial_data.py

:: Start server
echo.
echo ==============================
echo  Serveur lance sur :
echo  http://localhost:8000
echo ==============================
echo.
python manage.py runserver
