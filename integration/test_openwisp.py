"""Prova d'integrazione con un OpenWISP vero (openwisp-controller 1.3.x).

Gira nel progetto di test di openwisp-controller, con questo pacchetto in
INSTALLED_APPS dopo openwisp_controller.config: vedi integration/README.md e il
job «integration» della CI.
"""

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from swapper import load_model

from openwisp_luci_theme.admin import LuciThemeForm
from openwisp_luci_theme.models import OrganizationLuciTheme

Organization = load_model("openwisp_users", "Organization")
OrganizationUser = load_model("openwisp_users", "OrganizationUser")
Device = load_model("config", "Device")
Config = load_model("config", "Config")
Template = load_model("config", "Template")

TEMPLATE_JSON = Path(__file__).with_name("luci-theme-ninux.json")
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'

GLOBAL_CONTEXT = {
    "luci_logo": "/luci-static/ninux/logo.svg",
    "luci_brand": "ninux",
    "luci_accent": "",
    "luci_accent_dark": "",
    "luci_mode": "basic",
    "luci_allow_advanced": "1",
}


def uci(device):
    """Configurazione UCI generata per il device, riletta dal database come
    in una richiesta vera (l'oggetto in memoria tiene la configurazione gia'
    calcolata)."""
    return Config.objects.get(device=device).backend_instance.render()


@override_settings(OPENWISP_CONTROLLER_CONTEXT=GLOBAL_CONTEXT)
class LuciThemeIntegrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        from openwisp_controller.config import settings as controller_settings

        controller_settings.CONTEXT = GLOBAL_CONTEXT
        data = json.loads(TEMPLATE_JSON.read_text())
        cls.template = Template.objects.create(
            name="Tema LuCI ninux", backend=data["backend"], type="generic", config=data["config"]
        )
        cls.org_a = Organization.objects.create(name="Org A", slug="org-a")
        cls.org_b = Organization.objects.create(name="Org B", slug="org-b")
        cls.dev_a = cls._device(cls.org_a, "router-a", "00:11:22:33:44:01")
        cls.dev_b = cls._device(cls.org_b, "router-b", "00:11:22:33:44:02")

    @classmethod
    def _device(cls, org, name, mac):
        device = Device.objects.create(organization=org, name=name, mac_address=mac)
        config = Config.objects.create(device=device, backend="netjsonconfig.OpenWrt", config={})
        config.templates.add(cls.template)
        return device

    def _theme(self, org, files=None, **data):
        instance = OrganizationLuciTheme.objects.filter(organization=org).first()
        form = LuciThemeForm(data={**data}, files=files or {}, instance=instance)
        self.assertTrue(form.is_valid(), form.errors)
        theme = form.save(commit=False)
        theme.organization = org
        theme.save()
        return theme

    def test_global_context_without_theme(self):
        out = uci(self.dev_a)
        self.assertIn("option brand 'ninux'", out)
        self.assertIn("option logo '/luci-static/ninux/logo.svg'", out)
        self.assertIn("option default_mode 'basic'", out)
        self.assertIn("option allow_advanced '1'", out)
        self.assertNotIn("option accent", out)

    def test_theme_applies_only_to_its_organization(self):
        self._theme(
            self.org_a,
            files={"logo_file": SimpleUploadedFile("logo.svg", SVG, "image/svg+xml")},
            brand="Org A",
            accent="#0b5394",
            default_mode="advanced",
            allow_advanced="",
        )
        out_a = uci(self.dev_a)
        self.assertIn("option brand 'Org A'", out_a)
        self.assertIn("option logo 'data:image/svg+xml;base64,", out_a)
        self.assertIn("option accent '#0b5394'", out_a)
        self.assertIn("option default_mode 'advanced'", out_a)
        # campo vuoto: resta il valore globale
        self.assertIn("option allow_advanced '1'", out_a)
        # l'altra organizzazione non cambia
        out_b = uci(self.dev_b)
        self.assertIn("option brand 'ninux'", out_b)
        self.assertIn("option logo '/luci-static/ninux/logo.svg'", out_b)

    def test_device_variables_win(self):
        self._theme(self.org_a, brand="Org A", default_mode="advanced")
        config = self.dev_a.config
        config.context = {"luci_mode": "basic"}
        config.full_clean()
        config.save()
        out = uci(self.dev_a)
        self.assertIn("option default_mode 'basic'", out)
        self.assertIn("option brand 'Org A'", out)

    def test_saving_theme_changes_checksum(self):
        config = self.dev_a.config
        config.refresh_from_db()
        before = config.checksum
        with self.captureOnCommitCallbacks(execute=True):
            self._theme(self.org_a, brand="Nuovo nome")
        config = Config.objects.get(pk=config.pk)
        self.assertNotEqual(config.checksum, before)
        self.assertEqual(config.status, "modified")
        self.assertEqual(config.get_cached_checksum(), config.checksum)

    def test_remove_logo(self):
        self._theme(self.org_a, files={"logo_file": SimpleUploadedFile("l.svg", SVG)})
        self._theme(self.org_a, logo_remove="on")
        self.assertIn("option logo '/luci-static/ninux/logo.svg'", uci(self.dev_a))

    def test_logo_validation(self):
        cases = {
            "svg_unsafe": SVG.replace(b"<rect", b"<script>alert(1)</script><rect"),
            "format": b"plain text, not an image",
            "too_large": SVG + b" " * 40000,
        }
        for code, content in cases.items():
            with self.subTest(code=code):
                form = LuciThemeForm(data={}, files={"logo_file": SimpleUploadedFile("x.svg", content)})
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors.as_data()["logo_file"][0].code, code)

    def test_invalid_color(self):
        form = LuciThemeForm(data={"accent": "red"})
        self.assertFalse(form.is_valid())
        self.assertIn("accent", form.errors)

    def test_inline_in_organization_admin(self):
        User = get_user_model()
        admin = User.objects.create_superuser("root", "root@example.com", "pass")
        self.client.force_login(admin)
        url = reverse("admin:openwisp_users_organization_change", args=[self.org_a.pk])
        response = self.client.get(url)
        self.assertContains(response, "LuCI theme of the routers")
        self.assertContains(response, 'name="luci_theme-0-logo_file"')
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_organization_administrator_permissions(self):
        group = Group.objects.get(name="Administrator")
        perms = group.permissions.filter(content_type__app_label="openwisp_luci_theme")
        codenames = set(perms.values_list("codename", flat=True))
        self.assertEqual(
            codenames,
            {
                "add_organizationlucitheme",
                "change_organizationlucitheme",
                "delete_organizationlucitheme",
                "view_organizationlucitheme",
            },
        )
        self.assertTrue(Permission.objects.filter(codename="view_organizationlucitheme").exists())
        self.assertIn(
            "view_organizationlucitheme",
            Group.objects.get(name="Operator").permissions.values_list("codename", flat=True),
        )


def _errors(response):
    """Errori del form, per capire perche' un salvataggio non e' andato."""
    context = getattr(response, "context", None)
    return context.get("errors") if context else None


def _form_data(response):
    """Dati POST come li manderebbe il browser dalla pagina di modifica."""
    data = {}
    forms = [response.context["adminform"].form]
    for inline in response.context["inline_admin_formsets"]:
        formset = inline.formset
        forms.append(formset.management_form)
        forms.extend(formset.forms)
    for form in forms:
        for name, field in form.fields.items():
            value = form[name].value()
            if value is None or getattr(field.widget, "input_type", "") == "file":
                continue
            if isinstance(value, (list, tuple)):
                data[form.add_prefix(name)] = [str(v) for v in value]
            elif isinstance(value, bool):
                if value:
                    data[form.add_prefix(name)] = "on"
            else:
                data[form.add_prefix(name)] = str(value)
    return data


@override_settings(OPENWISP_CONTROLLER_CONTEXT=GLOBAL_CONTEXT)
class OrganizationAdminPostTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser("root", "root@example.com", "pass")
        self.client.force_login(self.admin)
        self.org = Organization.objects.create(name="Org C", slug="org-c")
        self.url = reverse("admin:openwisp_users_organization_change", args=[self.org.pk])

    def test_saving_organization_without_theme_creates_nothing(self):
        data = _form_data(self.client.get(self.url))
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302, _errors(response))
        self.assertFalse(OrganizationLuciTheme.objects.filter(organization=self.org).exists())

    def test_upload_logo_from_organization_page(self):
        data = _form_data(self.client.get(self.url))
        data["luci_theme-0-brand"] = "Org C"
        data["luci_theme-0-logo_file"] = SimpleUploadedFile("c.svg", SVG, "image/svg+xml")
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302, _errors(response))
        theme = OrganizationLuciTheme.objects.get(organization=self.org)
        self.assertEqual(theme.brand, "Org C")
        self.assertTrue(theme.logo.startswith("data:image/svg+xml;base64,"))
        self.assertEqual(theme.logo_name, "c.svg")
        # la pagina mostra l'anteprima del logo caricato
        self.assertContains(self.client.get(self.url), "c.svg")

    def test_rejected_logo_shows_error(self):
        data = _form_data(self.client.get(self.url))
        data["luci_theme-0-logo_file"] = SimpleUploadedFile("x.svg", b"<svg><script>x</script></svg>")
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "scripts, event handlers or external references")
        self.assertFalse(OrganizationLuciTheme.objects.filter(organization=self.org).exists())
