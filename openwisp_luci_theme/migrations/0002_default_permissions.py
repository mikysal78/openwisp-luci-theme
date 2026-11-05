"""Permessi del tema ai gruppi predefiniti di OpenWISP.

Administrator: aggiunge, modifica, elimina e vede il tema della propria
organizzazione; Operator: lo vede soltanto. I gruppi li crea openwisp-users:
se mancano (installazione personalizzata) non si fa niente.
"""

import swapper
from django.contrib.auth.management import create_permissions
from django.db import migrations

GROUPS = {
    "Administrator": ("add", "change", "delete", "view"),
    "Operator": ("view",),
}


def assign_permissions(apps, schema_editor):
    # I permessi nascono al post_migrate: qui servono subito
    app_config = apps.get_app_config("openwisp_luci_theme")
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for name, actions in GROUPS.items():
        group = Group.objects.filter(name=name).first()
        if group is None:
            continue
        codenames = ["%s_organizationlucitheme" % action for action in actions]
        group.permissions.add(
            *Permission.objects.filter(content_type__app_label="openwisp_luci_theme", codename__in=codenames)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("openwisp_luci_theme", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        # crea i gruppi Administrator e Operator
        swapper.dependency("openwisp_users", "Organization", version="0004_default_groups"),
    ]

    operations = [migrations.RunPython(assign_permissions, migrations.RunPython.noop)]
