import base64

import pytest

from openwisp_luci_theme.logo import LogoError, data_uri_size, detect_type, to_data_uri

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.mark.parametrize(
    "data,mime",
    [
        (SVG, "image/svg+xml"),
        (b'<?xml version="1.0"?>\n' + SVG, "image/svg+xml"),
        (b"\xef\xbb\xbf<!-- logo -->\n" + SVG, "image/svg+xml"),
        (PNG, "image/png"),
        (b"\xff\xd8\xff\xe0" + b"\x00" * 16, "image/jpeg"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 8, "image/webp"),
        (b"GIF89a" + b"\x00" * 8, "image/gif"),
        (b"plain text", None),
        (b"<html><body>no svg</body></html>", None),
    ],
)
def test_detect_type(data, mime):
    assert detect_type(data) == mime


def test_data_uri_roundtrip():
    uri = to_data_uri(SVG, 1024)
    assert uri.startswith("data:image/svg+xml;base64,")
    assert base64.b64decode(uri.split(",", 1)[1]) == SVG
    assert data_uri_size(uri) == len(SVG)


def test_png_data_uri():
    assert to_data_uri(PNG, 1024).startswith("data:image/png;base64,")


@pytest.mark.parametrize(
    "data,code",
    [
        (b"", "empty"),
        (SVG + b" " * 2000, "too_large"),
        (b"not an image", "format"),
        (SVG.replace(b"<rect", b"<script>alert(1)</script><rect"), "svg_unsafe"),
        (SVG.replace(b"<rect", b'<rect onload="x()"'), "svg_unsafe"),
        (SVG.replace(b"<rect", b'<a href="javascript:x()"><rect/></a><rect'), "svg_unsafe"),
        (SVG.replace(b"<rect", b'<image href="https://example.com/x.png"/><rect'), "svg_unsafe"),
        (SVG.replace(b"<rect", b"<foreignObject><p>x</p></foreignObject><rect"), "svg_unsafe"),
        (b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY x "y">]>' + SVG, "svg_unsafe"),
    ],
)
def test_rejected(data, code):
    with pytest.raises(LogoError) as exc:
        to_data_uri(data, 1024)
    assert exc.value.code == code


def test_internal_references_are_allowed():
    svg = SVG.replace(b"<rect", b'<defs><path id="p" d="M0 0h1"/></defs><use href="#p"/><rect')
    assert to_data_uri(svg, 1024).startswith("data:image/svg+xml")


def test_data_uri_size_empty():
    assert data_uri_size("") == 0
    assert data_uri_size("not a data uri") == 0
