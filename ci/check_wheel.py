"""Controlla che il wheel contenga tutti i file necessari a runtime."""

import sys
import zipfile

REQUIRED = [
    "openwisp_luci_theme/__init__.py",
    "openwisp_luci_theme/admin.py",
    "openwisp_luci_theme/apps.py",
    "openwisp_luci_theme/context.py",
    "openwisp_luci_theme/logo.py",
    "openwisp_luci_theme/models.py",
    "openwisp_luci_theme/settings.py",
    "openwisp_luci_theme/variables.py",
    "openwisp_luci_theme/migrations/__init__.py",
    "openwisp_luci_theme/migrations/0001_initial.py",
    "openwisp_luci_theme/migrations/0002_default_permissions.py",
    "openwisp_luci_theme/locale/it/LC_MESSAGES/django.mo",
]

names = set(zipfile.ZipFile(sys.argv[1]).namelist())
missing = [name for name in REQUIRED if name not in names]
if missing:
    sys.exit("missing from the wheel: " + ", ".join(missing))
print("wheel ok: %d files" % len(names))
