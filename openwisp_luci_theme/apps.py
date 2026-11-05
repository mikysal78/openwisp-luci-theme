from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save
from django.utils.translation import gettext_lazy as _


class LuciThemeConfig(AppConfig):
    name = "openwisp_luci_theme"
    label = "openwisp_luci_theme"
    verbose_name = _("LuCI theme")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from swapper import load_model

        from .context import luci_theme_context, theme_changed
        from .models import OrganizationLuciTheme

        Config = load_model("config", "Config")
        Config.register_context_function(luci_theme_context)

        uid = "openwisp_luci_theme_%s"
        post_save.connect(theme_changed, sender=OrganizationLuciTheme, dispatch_uid=uid % "save")
        post_delete.connect(theme_changed, sender=OrganizationLuciTheme, dispatch_uid=uid % "delete")
