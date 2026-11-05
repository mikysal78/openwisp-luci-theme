#!/bin/sh
# Prova d'integrazione con un OpenWISP vero: scarica il progetto di test di
# openwisp-controller alla versione indicata, ci aggiunge questo pacchetto e
# lancia integration/test_openwisp.py e il controllo delle migrazioni.
#
# Serve un Python con openwisp-controller (stessa versione) gia' installato e
# SpatiaLite (Debian/Ubuntu: libsqlite3-mod-spatialite). Uso:
#
#   integration/run.sh [versione-openwisp-controller] [cartella-di-lavoro]
set -eu

VERSION=${1:-1.3.2}
WORK=${2:-${TMPDIR:-/tmp}/openwisp-luci-theme-integration}
REPO=$(cd "$(dirname "$0")/.." && pwd)

if [ ! -d "$WORK/owc" ]; then
	mkdir -p "$WORK"
	git clone -q --depth 1 --branch "$VERSION" https://github.com/openwisp/openwisp-controller.git "$WORK/owc"
fi
cd "$WORK/owc/tests"

# Redis non serve: cache, sessioni e canali in memoria, celery sincrono
cat > openwisp2/local_settings.py <<EOF
import sys as _sys
_sys.path.insert(0, "$REPO")
from .settings import INSTALLED_APPS as _apps  # noqa: E402
INSTALLED_APPS = list(_apps) + ["openwisp_luci_theme"]
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "sessions": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "sessions"},
}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
EOF
ln -sfn "$REPO/integration" luci_theme_integration

python manage.py makemigrations openwisp_luci_theme --check --dry-run
python manage.py test luci_theme_integration --parallel 1 --noinput
