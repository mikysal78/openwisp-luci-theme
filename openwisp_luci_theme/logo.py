"""Logo del tema: controllo del file caricato e conversione in data: URI.

Il logo arriva al router dentro la configurazione (opzione UCI luci.ninux.logo)
come data: URI, non come link: cosi' si vede anche quando chi apre LuCI non
raggiunge Internet ne' il server OpenWISP, e non serve servire file pubblici.

Il prezzo e' il peso: il data: URI finisce in /etc/config/luci e in ogni pagina
di LuCI, per questo c'e' un limite di dimensione (vedi settings.py) e conviene
un SVG piccolo.

Nessuna dipendenza da Django: le funzioni sollevano LogoError con un codice, il
form dell'admin lo traduce in un messaggio.
"""

import base64
import re

# (tipo MIME, controllo sui primi byte)
_RASTER = (
    ("image/png", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    ("image/webp", lambda b: len(b) > 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
    ("image/gif", lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
)

# Nell'header di LuCI il logo e' un <img>, dove gli script di un SVG non girano
# comunque. Li rifiutiamo lo stesso: il file resta salvato nel database e un
# SVG con script o riferimenti esterni non ha motivo di esserci.
_SVG_FORBIDDEN = re.compile(
    rb"<\s*script|<\s*foreignObject|\bon[a-z]+\s*=|javascript:|<!ENTITY|"
    rb"(?:xlink:)?href\s*=\s*[\"']\s*(?!#|data:image/)",
    re.IGNORECASE,
)
_SVG_ROOT = re.compile(rb"<svg[\s>]", re.IGNORECASE)


class LogoError(ValueError):
    """Logo non valido. ``code``: too_large, empty, format, svg_unsafe."""

    def __init__(self, code, **params):
        super().__init__(code)
        self.code = code
        self.params = params


def detect_type(data):
    """Tipo MIME del logo dai suoi byte (non dal nome o dal browser)."""
    for mime, check in _RASTER:
        if check(data):
            return mime
    head = data[:2048].lstrip(b"\xef\xbb\xbf \t\r\n")
    if head.startswith((b"<?xml", b"<svg", b"<!--")) and _SVG_ROOT.search(data):
        return "image/svg+xml"
    return None


def to_data_uri(data, max_size):
    """Controlla il logo e lo restituisce come data: URI base64."""
    if not data:
        raise LogoError("empty")
    if len(data) > max_size:
        raise LogoError("too_large", size=len(data), max_size=max_size)
    mime = detect_type(data)
    if mime is None:
        raise LogoError("format")
    if mime == "image/svg+xml" and _SVG_FORBIDDEN.search(data):
        raise LogoError("svg_unsafe")
    return "data:%s;base64,%s" % (mime, base64.b64encode(data).decode("ascii"))


def data_uri_size(uri):
    """Dimensione in byte del file contenuto in un data: URI base64."""
    if not uri or "," not in uri:
        return 0
    payload = uri.split(",", 1)[1]
    return len(payload) * 3 // 4 - payload.count("=")
