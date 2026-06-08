# Linux Screen Recorder

Records screen with system audio (PulseAudio monitor), region selection, and system tray indicator.

## Dependencies

### System packages

```bash
sudo apt install ffmpeg slop xclip xdotool x11-utils xinput libnotify-bin pulseaudio-utils
```

### Python packages

```bash
pip install pystray Pillow python-xlib
```

## Usage

Run:

```bash
python3 screen_recorder.py
```

Press **Ctrl+Shift+Print Screen** to select a region and start recording. Press the same shortcut again to stop. The recording is saved to `~/Videos/` and the file path is copied to your clipboard.

To use a different shortcut, pass `--shortcut`:

```bash
python3 screen_recorder.py --shortcut super+r             # Super+R to toggle
python3 screen_recorder.py --shortcut ctrl+alt+f5         # Ctrl+Alt+F5
python3 screen_recorder.py --shortcut print_screen        # Just Print Screen
```

### Options

| Flag | Description |
|------|-------------|
| `--shortcut`, `-s` | Custom hotkey (default: `ctrl+shift+print_screen`). Format: `mod+key` — modifiers: `ctrl`, `shift`, `alt`, `super`; keys: `print_screen`, `f1`–`f12`, `esc`, `space`, `enter`, `tab`, `home`, `end`, `delete`, `insert`, `page_up`, `page_down`, arrows (`up`, `down`, `left`, `right`), or any single character |
| `--log-file`, `-l` | Log output to a file (useful for autostart) |

### Autostart (start on login)

Add to **Startup Applications** (GNOME Tweaks or `gnome-session-properties`):

```
Name: Screen Recorder
Command: python3 /path/to/screen_recorder.py --log-file ~/.local/share/screen-recorder/log
```

The tray icon appears in your system tray. Right-click to start/stop recording or quit.
