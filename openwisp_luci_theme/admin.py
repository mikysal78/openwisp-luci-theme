"""Riquadro «LuCI theme» nella pagina dell'organizzazione.

Si aggiunge come inline all'admin dell'organizzazione gia' registrato da
openwisp-users (ed esteso da openwisp-controller con le Config settings): per
questo l'app va in INSTALLED_APPS dopo openwisp_controller.config.

Chi vede e modifica il riquadro: i superuser e chi ha i permessi del modello
(la migrazione li da' al gruppo Administrator di OpenWISP), sempre solo sulle
organizzazioni che l'admin gli lascia aprire.
"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from swapper import load_model

from . import settings as app_settings
from .logo import LogoError, to_data_uri
from .models import OrganizationLuciTheme

Organization = load_model("openwisp_users", "Organization")

try:
    BaseOrganizationAdmin = type(admin.site._registry[Organization])
except KeyError as e:
    raise ImproperlyConfigured(
        "openwisp_luci_theme va messo in INSTALLED_APPS dopo openwisp_users e openwisp_controller.config"
    ) from e

LOGO_ACCEPT = "image/svg+xml,image/png,image/jpeg,image/webp,image/gif"

LOGO_ERRORS = {
    "empty": _("The file is empty."),
    "too_large": _("The logo is larger than %(max_size)s: use a smaller image (an SVG is ideal)."),
    "format": _("Unsupported file: upload an SVG, PNG, JPEG, WebP or GIF image."),
    "svg_unsafe": _(
        "The SVG contains scripts, event handlers or external references: remove them and try again."
    ),
}


class LuciThemeForm(forms.ModelForm):
    logo_file = forms.FileField(
        label=_("Upload logo"),
        required=False,
        help_text=_(
            "SVG (recommended), PNG, JPEG, WebP or GIF, at most %(max)s. It is sent to the routers "
            "inside their configuration, so it is shown even without Internet access."
        )
        % {"max": filesizeformat(app_settings.MAX_LOGO_SIZE)},
        widget=forms.ClearableFileInput(attrs={"accept": LOGO_ACCEPT}),
    )
    logo_remove = forms.BooleanField(
        label=_("Remove logo"),
        required=False,
        help_text=_("Go back to the logo of the global setting (Ninux by default)."),
    )

    class Meta:
        model = OrganizationLuciTheme
        fields = (
            "logo_file",
            "logo_remove",
            "brand",
            "accent",
            "accent_dark",
            "default_mode",
            "allow_advanced",
        )
        widgets = {
            "accent": forms.TextInput(attrs={"placeholder": "#d93d1c", "size": 9}),
            "accent_dark": forms.TextInput(attrs={"placeholder": "#ff6a45", "size": 9}),
        }

    def clean_logo_file(self):
        upload = self.cleaned_data.get("logo_file")
        if not upload:
            return None
        data = upload.read(app_settings.MAX_LOGO_SIZE + 1)
        try:
            self._logo_uri = to_data_uri(data, app_settings.MAX_LOGO_SIZE)
        except LogoError as e:
            params = {"max_size": filesizeformat(app_settings.MAX_LOGO_SIZE)}
            raise ValidationError(LOGO_ERRORS[e.code], code=e.code, params=params) from e
        self._logo_name = (upload.name or "")[-255:]
        return upload

    def save(self, commit=True):
        instance = super().save(commit=False)
        if getattr(self, "_logo_uri", None):
            instance.logo = self._logo_uri
            instance.logo_name = self._logo_name
        elif self.cleaned_data.get("logo_remove"):
            instance.logo = ""
            instance.logo_name = ""
        if commit:
            instance.save()
        return instance


class LuciThemeInline(admin.StackedInline):
    model = OrganizationLuciTheme
    form = LuciThemeForm
    extra = 1
    max_num = 1
    can_delete = True
    verbose_name = _("LuCI theme of the routers")
    verbose_name_plural = _("LuCI theme of the routers")
    readonly_fields = ("current_logo",)
    fieldsets = (
        (
            None,
            {
                "description": _(
                    "Logo, name and colors of LuCI on the routers of this organization, and its "
                    "Basic/Advanced mode. Empty fields keep the global setting. It applies to routers "
                    "with the «Tema LuCI ninux» template and the luci-theme-ninux package; variables "
                    "set on a single device still win."
                ),
                "fields": (
                    "current_logo",
                    "logo_file",
                    "logo_remove",
                    "brand",
                    ("accent", "accent_dark"),
                    "default_mode",
                    "allow_advanced",
                ),
            },
        ),
    )

    @admin.display(description=_("current logo"))
    def current_logo(self, obj):
        if not obj or not obj.logo:
            return _("Global setting (Ninux logo by default)")
        return format_html(
            '<img src="{}" alt="" style="max-height:40px;max-width:240px;background:#fff;'
            'padding:6px;border:1px solid #ddd;border-radius:6px;vertical-align:middle"> '
            '<span style="margin-left:.5em;color:#666">{} · {}</span>',
            obj.logo,
            obj.logo_name or "logo",
            filesizeformat(obj.logo_size),
        )


inlines = list(BaseOrganizationAdmin.inlines)
if LuciThemeInline not in inlines:
    BaseOrganizationAdmin.inlines = inlines + [LuciThemeInline]
