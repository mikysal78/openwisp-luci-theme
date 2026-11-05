# Changelog

## 0.1.1

- The help text of the logo upload gives the size: LuCI shows the logo 28
  pixels high and at most 220 wide (24 × 150 on phones); for raster images,
  56 × 440 at most (double size, for high-density screens).

## 0.1.0

- First release: **LuCI theme of the routers** box on the organization page,
  with logo upload (SVG, PNG, JPEG, WebP, GIF; sent to the routers as a
  `data:` URI), name, accent colors, initial mode and Basic/Advanced switch.
- The settings reach the devices of the organization as the `luci_*`
  variables of the **Tema LuCI ninux** template, through
  `Config.register_context_function`; empty fields keep the global value and
  device variables still win.
- Saving or deleting the box recomputes the configuration checksums of the
  organization's devices.
- Permissions for the OpenWISP Administrator (full) and Operator (view) groups.
- Italian translation.
