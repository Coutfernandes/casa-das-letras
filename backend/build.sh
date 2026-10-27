#!/usr/bin/env bash
# Build do backend no Render: roda a cada deploy, antes de o Daphne iniciar.

# Para no primeiro comando que falhar: um deploy pela metade não sobe.
set -o errexit

pip install -r requirements.txt

# Junta o CSS e o JS do admin em staticfiles/, de onde o WhiteNoise serve.
python manage.py collectstatic --no-input

# Aplica no Neon as migrations novas.
python manage.py migrate
