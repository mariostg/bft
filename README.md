# Quick Start

bft git clone https://github.com/mariostg/bft.git
cd bft
python -m venv .env-bft
source .env-bft/bin/activate
python -m pip install pip-tools
pip-compile
pip-sync --ask
cp .env-exemple .env #Edit as needed
mkdir log # adapt settings.py accorfingly
python manage.py createsuperuser.
python manage.py runserver
