# Display Switcher

A small tray daemon that automatically switches the **primary display** (and the
matching audio output) depending on which monitor is currently powered on.

The tool is built around one constraint: the desktop monitor on `DP-1` reports a
reliable connection state, while the TV on HDMI does **not** (there is no CEC on
this setup). So the state of `DP-1` is treated as the source of truth:

- `DP-1` present/connected → **DESKTOP** mode (desktop monitor + desktop speakers)
- `DP-1` gone (monitor powered off, drops off the connector list) → **TV** mode
  (HDMI output + HDMI audio)

A background daemon polls the display state once per second and, on change,
switches both the display layout and the default audio sink, retrying a few times
if the target isn't ready yet.

## Supported environments

| Platform | Display control | Audio control |
|----------|-----------------|---------------|
| KDE Plasma (Wayland) | `kscreen-doctor` | PipeWire (`wpctl`) |
| GNOME / Mutter (Wayland) | `gnome-monitor-config` | PipeWire (`wpctl`) |
| Windows | `DisplaySwitch.exe` | `svcl.exe` |

On Linux the desktop environment is detected automatically: first from
`XDG_CURRENT_DESKTOP`, then by falling back to whichever of `kscreen-doctor` /
`gnome-monitor-config` is installed. Audio switching goes through PipeWire and is
shared between KDE and GNOME.

## HDMI connector naming: `HDMI-1` vs `HDMI-A-1`

The same physical HDMI port is reported under **different connector names**
depending on the compositor:

- **KDE / `kscreen-doctor`** reports it as `HDMI-A-1`
- **GNOME / `gnome-monitor-config`** reports it as `HDMI-1`

`DP-1` is identical on both. Because of this each backend keeps its own connector
constants — see `HDMI` in `src/backends/kde.py` (`HDMI-A-1`) and `src/backends/gnome.py`
(`HDMI-1`). If you adapt this tool to your own hardware, list your outputs with
`kscreen-doctor -o` (KDE) or `gnome-monitor-config list` (GNOME) and adjust those
constants accordingly.

## Configuration

Everything is hardcoded to one setup, so adjust the constants for your machine:

- **Display connectors** — `DP` / `HDMI` in `src/backends/kde.py` and
  `src/backends/gnome.py`.
- **Audio sinks** — `SINK_DESKTOP` / `SINK_TV` in `src/backends/linux.py`. List the
  available sink names with `wpctl status`.
- **Windows devices** — `device_map` and the display name check in
  `src/backends/windows.py`.

## Project layout

```
display_switcher.sh  launcher
src/
  main.py            entry point: logging, backend selection, tray + daemon
  daemon.py          polling loop, applies display/audio changes on mode change
  tray_icon.py       system tray icon + log viewer toggle
  log_viewer.py      simple log window
  modes/enums.py     DisplayMode (DESKTOP / TV)
  backends/
    base.py          Backend abstract interface
    linux.py         LinuxBackend: shared PipeWire audio
    kde.py           KdeBackend: kscreen-doctor display control
    gnome.py         GnomeBackend: gnome-monitor-config display control
    windows.py       WindowsBackend
```

## Running

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python src/main.py
```

Or use the helper script:

```bash
./display_switcher.sh
```

Logs are written to `display_switcher.log` and can be viewed from the tray icon.
