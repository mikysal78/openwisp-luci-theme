"""Variabili di configurazione del tema (senza dipendenze da Django).

Sono le stesse del template OpenWISP «Tema LuCI ninux» (repo openwisp2,
openwisp-templates/luci-theme-ninux.json). Un campo vuoto non produce la
variabile: vale il valore che viene da piu' in alto (contesto globale del
playbook, variabili dell'organizzazione o del gruppo).
"""

import re

COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

MODES = ("basic", "advanced")

# nome del campo del modello -> variabile del template
FIELDS = (
    ("logo", "luci_logo"),
    ("brand", "luci_brand"),
    ("accent", "luci_accent"),
    ("accent_dark", "luci_accent_dark"),
    ("default_mode", "luci_mode"),
    ("allow_advanced", "luci_allow_advanced"),
)


def build_context(values):
    """Dalle impostazioni (dict campo -> valore) alle variabili del template."""
    context = {}
    for field, variable in FIELDS:
        value = values.get(field)
        if value is None or value == "":
            continue
        context[variable] = str(value).strip()
    return context
