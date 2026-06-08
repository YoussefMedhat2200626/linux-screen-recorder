# Linux Screen Recorder

Lightweight screen recorder for Ubuntu/Linux. Select any area on screen and record it with system audio.

## How to install

Open a terminal and run these commands one by one:

```bash
sudo apt install ffmpeg slop xclip xdotool x11-utils xinput libnotify-bin pulseaudio-utils
pip install pystray Pillow python-xlib
```

## How to use

**Step 1:** Run the app

```bash
python3 screen_recorder.py
```

**Step 2:** Press **Ctrl + Shift + Print Screen**

Your mouse cursor will turn into a crosshair. Click and drag to select the area you want to record.

**Step 3:** Press **Ctrl + Shift + Print Screen** again to stop

The recording is saved to `~/Videos/` and copied to your clipboard — just press **Ctrl + V** anywhere to share it.

## Change the shortcut

Don't like the default key? Use `--shortcut`:

```bash
python3 screen_recorder.py --shortcut super+r           # Windows key + R
python3 screen_recorder.py --shortcut ctrl+alt+f5       # Ctrl + Alt + F5
python3 screen_recorder.py --shortcut print_screen      # Just Print Screen
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
