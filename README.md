# Linux Screen Recorder

Lightweight screen recorder for Ubuntu/Linux with **Instant Replay** (like NVIDIA ShadowPlay).

Select any area on screen and record it with system audio — or keep a rolling 60-second buffer and save the last minute on demand.

## How to install

Open a terminal and run these commands one by one:

```bash
sudo apt install ffmpeg slop xclip xdotool x11-utils xinput libnotify-bin pulseaudio-utils python3-pystray python3-pil python3-xlib
```

### What each app does

| App | Purpose |
|-----|---------|
| `ffmpeg` | Records the screen and audio, encodes the video |
| `slop` | Lets you click and drag to select the area to record |
| `xclip` | Copies the video file to clipboard so you can paste it |
| `xdotool` | Gets your screen size |
| `x11-utils` | Provides `xdpyinfo` (fallback for screen size) |
| `xinput` | Listens for your shortcut keys |
| `libnotify-bin` | Shows desktop notifications ("Recording started", "Saved") |
| `pulseaudio-utils` | Provides `pactl` to find the system audio source |
| `python3-pystray` | Shows the red dot icon in the system tray |
| `python3-pil` | Draws the tray icon |
| `python3-xlib` | Detects which keys are pressed for the shortcut |

## How to use

**Step 1:** Kill any old instances, then run the app

```bash
pkill -f "python.*screen_recorder" 2>/dev/null
python3 ~/Desktop/screen_recorder.py
```

**Step 2 — Record a region:** Press **Ctrl + Shift + Print Screen**

Your mouse cursor will turn into a crosshair. Click and drag to select the area you want to record. Press the same shortcut again to stop.

**Step 3 — Instant Replay:** Press **Ctrl + Shift + F10**

Saves the last 60 seconds of your screen (with audio) to `~/Videos/instant_replay_*.mp4`. The buffer runs continuously in the background — press the shortcut anytime to capture what just happened.

Recordings are saved to `~/Videos/` and copied to your clipboard — just press **Ctrl + V** anywhere to share.

## Change shortcuts

Don't like the defaults? Use `--shortcut` and `--replay-shortcut`:

```bash
# Change record key to Super+R
python3 ~/Desktop/screen_recorder.py --shortcut super+r

# Change instant replay to Ctrl+Shift+End
python3 ~/Desktop/screen_recorder.py --replay-shortcut ctrl+shift+end

# Change buffer duration to 120 seconds
python3 ~/Desktop/screen_recorder.py --replay-duration 120

# Change both
python3 ~/Desktop/screen_recorder.py --shortcut print_screen --replay-shortcut ctrl+shift+end
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
