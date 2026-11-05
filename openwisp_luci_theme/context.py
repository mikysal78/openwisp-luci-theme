"""Variabili del tema nel contesto dei device e ricalcolo dei checksum.

openwisp-controller (Config.get_context) applica i contesti in quest'ordine:
globale -> organizzazione -> gruppo di device -> VPN -> funzioni registrate
(questa) -> variabili del device. Quindi il tema dell'organizzazione vince sulle
variabili di organizzazione e gruppo con lo stesso nome, mentre le variabili
scritte nel singolo device restano l'ultima parola.
"""

import logging

from django.db import transaction

logger = logging.getLogger(__name__)


def luci_theme_context(config):
    """Funzione di contesto registrata con Config.register_context_function."""
    from .models import OrganizationLuciTheme

    organization_id = getattr(config.device, "organization_id", None)
    if not organization_id:
        return {}
    theme = OrganizationLuciTheme.objects.filter(organization_id=organization_id).first()
    return theme.as_context() if theme else {}


def invalidate_organization(organization_id):
    """Ricalcola i checksum dei device dell'organizzazione (dopo il commit).

    Senza, i router continuerebbero a ricevere il checksum in cache e non
    scaricherebbero la configurazione con il tema nuovo. E' lo stesso task che
    openwisp-controller usa quando cambiano le variabili dell'organizzazione.
    """

    def run():
        try:
            from openwisp_controller.config.tasks import bulk_invalidate_config_get_cached_checksum
        except ImportError:  # pragma: no cover - openwisp-controller troppo vecchio
            logger.warning("openwisp-luci-theme: cannot invalidate config checksums")
            return
        bulk_invalidate_config_get_cached_checksum.delay({"device__organization_id": str(organization_id)})

    transaction.on_commit(run)


def theme_changed(sender, instance, **kwargs):
    invalidate_organization(instance.organization_id)
