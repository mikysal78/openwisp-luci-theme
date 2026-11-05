from django.conf import settings

# Dimensione massima del logo caricato, in byte. Il logo arriva al router come
# data: URI (circa +33% in base64) e finisce in ogni pagina di LuCI: un SVG
# di pochi KB e' l'ideale.
MAX_LOGO_SIZE = getattr(settings, "OPENWISP_LUCI_THEME_MAX_LOGO_SIZE", 32 * 1024)
