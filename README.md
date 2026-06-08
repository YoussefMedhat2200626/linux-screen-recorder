# Linux Screen Recorder

Lightweight screen recorder for Ubuntu/Linux. Select any area on screen and record it with system audio.

## How to install

Open a terminal and run these commands one by one:

```bash
sudo apt install ffmpeg slop xclip xdotool x11-utils xinput libnotify-bin pulseaudio-utils
pip install pystray Pillow python-xlib
```

### What each app does

| App | Purpose |
|-----|---------|
| `ffmpeg` | Records the screen and audio, encodes the video |
| `slop` | Lets you click and drag to select the area to record |
| `xclip` | Copies the video file to clipboard so you can paste it |
| `xdotool` | Gets your screen size |
| `x11-utils` | Provides `xdpyinfo` (fallback for screen size) |
| `xinput` | Listens for your shortcut key (e.g. Print Screen) |
| `libnotify-bin` | Shows desktop notifications ("Recording started", "Saved") |
| `pulseaudio-utils` | Provides `pactl` to find the system audio source |
| `pystray` (Python) | Shows the red dot icon in the system tray |
| `Pillow` (Python) | Draws the tray icon |
| `python-xlib` (Python) | Detects which keys are pressed for the shortcut |

## How to use

**Step 1:** Kill any old instances, then run the app

```bash
pkill -f "python.*screen_recorder" 2>/dev/null
python3 ~/Desktop/screen_recorder.py
```

**Step 2:** Press **Ctrl + Shift + Print Screen**

Your mouse cursor will turn into a crosshair. Click and drag to select the area you want to record.

**Step 3:** Press **Ctrl + Shift + Print Screen** again to stop

The recording is saved to `~/Videos/` and copied to your clipboard — just press **Ctrl + V** anywhere to share it.

## Change the shortcut

Don't like the default key? Use `--shortcut`:

```bash
pkill -f "python.*screen_recorder" 2>/dev/null
python3 ~/Desktop/screen_recorder.py --shortcut super+r

pkill -f "python.*screen_recorder" 2>/dev/null
python3 ~/Desktop/screen_recorder.py --shortcut print_screen
```

**Modifiers:** `ctrl`, `shift`, `alt`, `super` (Windows key)  
**Keys:** `print_screen`, `f1`–`f12`, `esc`, `space`, `enter`, arrows (`up`, `down`, `left`, `right`), or any letter

## Start automatically on login

1. Open **Startup Applications** from your app menu
2. Click **Add**
3. Fill in:
   - **Name:** Screen Recorder
   - **Command:** `python3 /home/goldest/Desktop/screen_recorder.py --log-file ~/.local/share/screen-recorder/log`
4. Click **Add**

A red dot icon will appear in your system tray when the app is running. Right-click it to start/stop recording.
