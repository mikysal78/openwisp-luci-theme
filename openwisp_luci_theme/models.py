from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from swapper import get_model_name

from .logo import data_uri_size
from .variables import COLOR_RE, FIELDS, build_context

_color_validator = RegexValidator(COLOR_RE, _("Use a color in the form #rgb or #rrggbb, e.g. #d93d1c."))


class OrganizationLuciTheme(models.Model):
    """Tema LuCI dei router di un'organizzazione (logo, nome, colori, modalita').

    Ogni campo vuoto lascia il valore che arriva da piu' in alto: contesto
    globale del playbook, variabili dell'organizzazione o del gruppo. Le
    variabili del singolo device vincono comunque su tutto.
    """

    MODE_CHOICES = (
        ("", _("As the global setting")),
        ("basic", _("Basic")),
        ("advanced", _("Advanced")),
    )
    ADVANCED_CHOICES = (
        ("", _("As the global setting")),
        ("1", _("Yes: the Basic/Advanced switch is shown")),
        ("0", _("No: Basic menu only")),
    )

    organization = models.OneToOneField(
        get_model_name("openwisp_users", "Organization"),
        on_delete=models.CASCADE,
        related_name="luci_theme",
        verbose_name=_("organization"),
    )
    logo = models.TextField(_("logo"), blank=True, editable=False)
    logo_name = models.CharField(_("logo file name"), max_length=255, blank=True, editable=False)
    brand = models.CharField(
        _("name"),
        max_length=64,
        blank=True,
        help_text=_("Alternative text of the logo, e.g. the name of the community."),
    )
    accent = models.CharField(
        _("accent color"),
        max_length=7,
        blank=True,
        validators=[_color_validator],
        help_text=_("Color of buttons, links and active menu items (light scheme), e.g. #d93d1c."),
    )
    accent_dark = models.CharField(
        _("accent color (dark scheme)"),
        max_length=7,
        blank=True,
        validators=[_color_validator],
        help_text=_("Used when the browser is in dark mode; if empty, the accent color above is used."),
    )
    default_mode = models.CharField(
        _("initial mode"),
        max_length=8,
        blank=True,
        choices=MODE_CHOICES,
        help_text=_("Mode LuCI opens with; everyone can then change it from the switch."),
    )
    allow_advanced = models.CharField(
        _("Advanced mode available"),
        max_length=1,
        blank=True,
        choices=ADVANCED_CHOICES,
        help_text=_("Basic mode simplifies the interface, it is not access control."),
    )
    modified = models.DateTimeField(_("modified"), auto_now=True)

    class Meta:
        verbose_name = _("LuCI theme")
        verbose_name_plural = _("LuCI theme")

    def __str__(self):
        return str(_("LuCI theme of %(org)s") % {"org": self.organization})

    @property
    def logo_size(self):
        return data_uri_size(self.logo)

    def as_context(self):
        """Variabili per il template «Tema LuCI ninux» (solo i campi impostati).

        Senza accent_dark il tema usa accent anche nello schema scuro.
        """
        return build_context({field: getattr(self, field) for field, _var in FIELDS})
