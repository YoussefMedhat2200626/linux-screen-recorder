#!/usr/bin/env python3
import subprocess
import datetime
import os
import sys
import signal
import argparse
import threading
import queue
import re

from Xlib import display as xdisplay, XK

try:
    import pystray
    from PIL import Image, ImageDraw
    HAVE_TRAY = True
except ImportError:
    HAVE_TRAY = False

# Key syms we need to identify keys and modifiers
SYM_LOOKUP = {
    XK.XK_Print: "print_screen",
    XK.XK_Control_L: "ctrl_l",
    XK.XK_Control_R: "ctrl_r",
    XK.XK_Shift_L: "shift_l",
    XK.XK_Shift_R: "shift_r",
    XK.XK_Alt_L: "alt_l",
    XK.XK_Alt_R: "alt_r",
    XK.XK_Super_L: "super_l",
    XK.XK_Super_R: "super_r",
}

MOD_SYMS = {
    "ctrl":   {XK.XK_Control_L, XK.XK_Control_R},
    "shift":  {XK.XK_Shift_L, XK.XK_Shift_R},
    "alt":    {XK.XK_Alt_L, XK.XK_Alt_R},
    "cmd":    {XK.XK_Super_L, XK.XK_Super_R},
    "super":  {XK.XK_Super_L, XK.XK_Super_R},
    "win":    {XK.XK_Super_L, XK.XK_Super_R},
}

KEY_SYM_MAP = {
    "print_screen": XK.XK_Print,
    "f1": XK.XK_F1,
    "f2": XK.XK_F2,
    "f3": XK.XK_F3,
    "f4": XK.XK_F4,
    "f5": XK.XK_F5,
    "f6": XK.XK_F6,
    "f7": XK.XK_F7,
    "f8": XK.XK_F8,
    "f9": XK.XK_F9,
    "f10": XK.XK_F10,
    "f11": XK.XK_F11,
    "f12": XK.XK_F12,
    "esc": XK.XK_Escape,
    "space": XK.XK_space,
    "enter": XK.XK_Return,
    "tab": XK.XK_Tab,
    "home": XK.XK_Home,
    "end": XK.XK_End,
    "insert": XK.XK_Insert,
    "delete": XK.XK_Delete,
    "page_up": XK.XK_Page_Up,
    "page_down": XK.XK_Page_Down,
    "up": XK.XK_Up,
    "down": XK.XK_Down,
    "left": XK.XK_Left,
    "right": XK.XK_Right,
    "pause": XK.XK_Pause,
    "menu": XK.XK_Menu,
}


def _char_sym(c):
    try:
        return XK.string_to_keysym(c)
    except Exception:
        return None


class XInputListener:
    def __init__(self, on_key):
        self._on_key = on_key
        self._proc = None
        self._running = False

    def start(self):
        self._running = True
        try:
            self._proc = subprocess.Popen(
                ["xinput", "test-xi2", "--root"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, bufsize=1
            )
            return True
        except Exception as e:
            print(f"[ERROR] Could not start xinput: {e}", flush=True)
            return False

    def read_loop(self):
        if not self._proc:
            return
        in_event = False
        detail = None
        for line in iter(self._proc.stdout.readline, ""):
            if not self._running:
                break
            line_stripped = line.strip()

            m = re.match(r'EVENT type (\d+) \((.*)\)', line_stripped)
            if m:
                event_type = int(m.group(1))
                event_name = m.group(2)
                in_event = True
                detail = None
                if event_name == "KeyPress":
                    self._current_type = "press"
                elif event_name == "KeyRelease":
                    self._current_type = "release"
                else:
                    self._current_type = None
                continue

            if in_event and line_stripped.startswith("detail:"):
                m = re.match(r'detail:\s*(\d+)', line_stripped)
                if m:
                    detail = int(m.group(1))
                    if self._current_type == "press":
                        self._on_key(detail, True)
                    elif self._current_type == "release":
                        self._on_key(detail, False)
                    self._current_type = None
                    in_event = False
                    continue

            if in_event and not line.startswith(" "):
                in_event = False

        self._proc.wait()

    def stop(self):
        self._running = False
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except Exception:
                self._proc.kill()


class ScreenRecorder:
    def __init__(self, output_dir=None, indicator=None):
        self.recording = False
        self._selecting = False
        self.output_dir = output_dir or os.path.expanduser("~/Videos")
        self._proc = None
        self._indicator = indicator
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_monitor_source(self):
        try:
            r = subprocess.run(["pactl", "list", "sources", "short"],
                               capture_output=True, text=True, timeout=3)
            for line in r.stdout.strip().split("\n"):
                if ".monitor" in line:
                    parts = line.split("\t")
                    if len(parts) > 1:
                        return parts[1]
        except Exception:
            pass
        return "default"

    def _select_region(self):
        try:
            r = subprocess.run(
                ["slop", "--bordersize=3", "--color=1,0.3,0,0.9"],
                capture_output=True, text=True, timeout=30
            )
            if r.returncode != 0 or not r.stdout.strip():
                return None
            s = r.stdout.strip()
            m = re.match(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)', s)
            if m:
                return int(m.group(3)), int(m.group(4)), int(m.group(1)), int(m.group(2))
        except Exception:
            pass
        return None

    def _get_display_geometry(self):
        try:
            r = subprocess.run(["xdotool", "getdisplaygeometry"],
                               capture_output=True, text=True, timeout=3)
            if r.returncode == 0:
                parts = r.stdout.strip().split()
                if len(parts) == 2:
                    return parts[0], parts[1]
        except Exception:
            pass
        try:
            r = subprocess.run(["xdpyinfo"], capture_output=True, text=True, timeout=3)
            for line in r.stdout.split("\n"):
                if "dimensions" in line:
                    parts = line.strip().split()[1].split("x")
                    return parts[0], parts[1]
        except Exception:
            pass
        return "1920", "1080"

    def start(self, region=None):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output_file = os.path.join(self.output_dir, f"recording_{ts}.mp4")
        self.recording = True

        audio_source = self._get_monitor_source()
        display = os.environ.get("DISPLAY", ":0")

        if region:
            x, y, w, h = region
            w = w if w % 2 == 0 else w + 1
            h = h if h % 2 == 0 else h + 1
            display_input = f"{display}.0+{x},{y}"
            size = f"{w}x{h}"
        else:
            w, h = self._get_display_geometry()
            display_input = f"{display}.0"
            size = f"{w}x{h}"

        print(f"[AUDIO SOURCE] {audio_source}  [REGION] {size}{'' if not region else f' @+{x},{y}'}")

        cmd = [
            "ffmpeg", "-y",
            "-f", "x11grab", "-s", size, "-i", display_input,
            "-f", "pulse", "-i", audio_source,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            self._output_file
        ]

        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )

        self._stderr_thread = threading.Thread(
            target=self._log_ffmpeg_errors, daemon=True
        )
        self._stderr_thread.start()

        print(f"[RECORDING] → {self._output_file}")
        notify("Recording", "Screen recording started", "critical")
        if self._indicator:
            self._indicator.cmd.put(("show",))

    def _log_ffmpeg_errors(self):
        for line in iter(self._proc.stderr.readline, b""):
            if b"error" in line.lower() or b"fail" in line.lower():
                print(f"[FFMPEG] {line.decode(errors='replace').strip()}", flush=True)

    def stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.stdin.write(b"q")
            self._proc.stdin.flush()
            self._proc.wait(timeout=5)

        self.recording = False

        self._check_audio()

        if self._indicator:
            self._indicator.cmd.put(("hide",))

        if os.path.exists(self._output_file):
            size = os.path.getsize(self._output_file)
            if size > 0:
                name = os.path.basename(self._output_file)
                _copy_to_clipboard(self._output_file)
                notify("Recording Saved", f"{name}  ({size / 1024:.0f} KB)")
                print(f"[SAVED] {self._output_file} ({size / 1024:.0f}KB)")
            else:
                print(f"[ERROR] File is empty")
        else:
            print(f"[ERROR] No output file")

    def _check_audio(self):
        try:
            r = subprocess.run(
                ["ffprobe", self._output_file],
                capture_output=True, text=True, timeout=5
            )
            if "Audio:" not in r.stderr:
                print("[WARNING] No audio stream in recording! Check PulseAudio monitor source.")
        except Exception:
            pass

    def cleanup(self):
        if self._proc and self._proc.poll() is None:
            self._proc.kill()
            self._proc.wait(timeout=3)
        self.recording = False

    def toggle(self):
        if self.recording:
            self.stop()
        elif self._selecting:
            return
        else:
            self._selecting = True
            region = self._select_region()
            self._selecting = False
            if region is None:
                notify("Recording Cancelled", "No region selected")
                print("[CANCELLED] No region selected")
                return
            self.start(region)


def _make_icon(recording=False):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if recording:
        cx, cy = size // 2, size // 2
        r = size // 2 - 4
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 40, 40, 255))
    else:
        cx, cy = size // 2, size // 2
        r = size // 2 - 4
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(100, 100, 100, 255), width=4)
    return img


class RecordingIndicator:
    def __init__(self):
        self.cmd = queue.Queue()
        self._recording = False
        self._icon = None

    def show(self):
        if self._recording:
            return
        self._recording = True
        if self._icon:
            self._icon.icon = _make_icon(True)
            self._icon.update_menu()

    def hide(self):
        if not self._recording:
            return
        self._recording = False
        if self._icon:
            self._icon.icon = _make_icon(False)
            self._icon.update_menu()

    def run(self):
        menu = (
            pystray.MenuItem("Start Recording", lambda: self.cmd.put(("toggle",)), visible=lambda: not self._recording),
            pystray.MenuItem("Stop Recording", lambda: self.cmd.put(("toggle",)), visible=lambda: self._recording),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: self.cmd.put(("quit",))),
        )
        icon = pystray.Icon("screen-recorder", _make_icon(False), "Screen Recorder", menu)
        self._icon = icon
        icon.run()


def _copy_to_clipboard(filepath):
    from urllib.parse import quote
    file_uri = f"file://{quote(filepath)}"
    uri_list = f"{file_uri}\r\n"

    try:
        subprocess.run(["xclip", "-selection", "clipboard", "-t", "text/uri-list"], input=uri_list.encode(), timeout=2)
        subprocess.run(["xclip", "-selection", "clipboard"], input=filepath.encode(), timeout=2)
    except FileNotFoundError:
        try:
            subprocess.run(["xsel", "-i", "-b"], input=uri_list.encode(), timeout=2)
        except Exception:
            pass
    except Exception:
        pass


def notify(title, body, urgency="normal"):
    try:
        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, body],
            timeout=2
        )
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Screen Recorder")
    parser.add_argument(
        "--shortcut", "-s",
        default="ctrl+shift+print_screen",
        help="Key or combo to toggle recording (default: ctrl+shift+print_screen)"
    )
    parser.add_argument(
        "--log-file", "-l",
        default=None,
        help="Log output to a file instead of stdout (useful for autostart)"
    )
    args = parser.parse_args()

    if args.log_file:
        log_dir = os.path.dirname(args.log_file) or "."
        os.makedirs(log_dir, exist_ok=True)
        sys.stdout = open(args.log_file, "a", buffering=1)
        sys.stderr = sys.stdout

    # Parse shortcut: ["ctrl", "shift", "print_screen"]
    parts = args.shortcut.lower().replace("-", "_").split("+")
    main_key_name = parts[-1]
    mod_names = parts[:-1]

    main_sym = KEY_SYM_MAP.get(main_key_name) or _char_sym(main_key_name)
    if main_sym is None:
        print(f"[ERROR] Unknown key: {main_key_name}", flush=True)
        sys.exit(1)

    # Required modifier sym sets
    req_mod_sym_sets = []
    for m in mod_names:
        s = MOD_SYMS.get(m, set())
        if s:
            req_mod_sym_sets.append(s)

    indicator = RecordingIndicator()
    recorder = ScreenRecorder(indicator=indicator)
    stop_event = threading.Event()
    pressed_mod_syms = set()

    disp = xdisplay.Display()

    def keycode_to_sym(kc):
        return disp.keycode_to_keysym(kc, 0)

    def cleanup_exit(sig=None, frame=None):
        print("\n[QUIT] Stopping...", flush=True)
        if recorder.recording:
            recorder.cleanup()
        indicator.hide()
        listener.stop()
        stop_event.set()
        os._exit(0)

    signal.signal(signal.SIGINT, cleanup_exit)
    signal.signal(signal.SIGTERM, cleanup_exit)

    def process_indicator():
        while not stop_event.is_set():
            try:
                cmd = indicator.cmd.get(timeout=0.3)
                if cmd[0] == "quit":
                    cleanup_exit(None, None)
                    break
                elif cmd[0] == "toggle":
                    recorder.toggle()
                elif cmd[0] == "show":
                    indicator.show()
                elif cmd[0] == "hide":
                    indicator.hide()
            except queue.Empty:
                continue

    def on_key(keycode, is_press):
        nonlocal pressed_mod_syms
        sym = keycode_to_sym(keycode)
        if sym is None:
            return

        # Track modifier keys
        if sym in MOD_SYMS.get("ctrl", set()) or \
           sym in MOD_SYMS.get("shift", set()) or \
           sym in MOD_SYMS.get("alt", set()) or \
           sym in MOD_SYMS.get("super", set()):
            for mod_set in MOD_SYMS.values():
                if sym in mod_set:
                    if is_press:
                        pressed_mod_syms.add(sym)
                    else:
                        pressed_mod_syms.discard(sym)

        if not is_press:
            return

        if sym != main_sym:
            return

        # All required modifiers must be pressed
        for needed_set in req_mod_sym_sets:
            if not pressed_mod_syms.intersection(needed_set):
                return

        recorder.toggle()

    notify("Screen Recorder", "Press Ctrl+Shift+Print Screen to select region and record")
    print("=== Screen Recorder (System Audio) ===", flush=True)
    print(f"Press  {args.shortcut}  to start / stop recording", flush=True)
    print("Press  Ctrl+C  to quit\n", flush=True)

    listener = XInputListener(on_key)
    if not listener.start():
        print("[ERROR] Failed to start key listener", flush=True)
        sys.exit(1)

    tray_thread = threading.Thread(target=indicator.run, daemon=True)
    tray_thread.start()

    try:
        listener.read_loop()
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    finally:
        listener.stop()


if __name__ == "__main__":
    main()
