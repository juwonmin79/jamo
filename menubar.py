from __future__ import annotations

import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import rumps

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from config import add_folder, list_folders, load_config, remove_folder, save_config
from normalizer import normalize_folder

INTERVAL_OPTIONS = {
    "1분":   60,
    "5분":   300,
    "10분":  600,
    "30분":  1800,
    "1시간": 3600,
    "6시간": 21600,
    "수동":  0,
}


class JasoMonApp(rumps.App):
    def __init__(self):
        super().__init__("", quit_button=None)
        self.icon = str(PROJECT_DIR / "jaso_menubar.png")
        self.template = True
        self._spinner_frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        self._spinner_idx = 0
        self._spinner_timer = None
        self._timer = None
        self._running = False
        self._last_result = ""
        self._build_menu()

    def _build_menu(self):
        self.menu.clear()

        status = rumps.MenuItem(self._last_result or "마지막 실행: 없음")
        status.set_callback(None)
        self.menu.add(status)
        self.menu.add(rumps.separator)

        self.menu.add(rumps.MenuItem("▶  지금 실행", callback=self._run_now))
        self.menu.add(rumps.separator)

        folder_menu = rumps.MenuItem("📁  폴더 관리")
        folders = list_folders()
        if folders:
            for f in folders:
                label = Path(f).name + "  ✓"
                item = rumps.MenuItem(label, callback=self._make_remove_callback(f))
                folder_menu.add(item)
            folder_menu.add(rumps.separator)
        folder_menu.add(rumps.MenuItem("＋  폴더 추가...", callback=self._add_folder))
        self.menu.add(folder_menu)
        self.menu.add(rumps.separator)

        config = load_config()
        current_interval = config.get("interval", 1800)
        interval_menu = rumps.MenuItem("⏱  실행 주기")
        for label, seconds in INTERVAL_OPTIONS.items():
            check = "✓  " if seconds == current_interval else "    "
            item = rumps.MenuItem(check + label, callback=self._make_interval_callback(seconds))
            interval_menu.add(item)
        self.menu.add(interval_menu)
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit Jaso-Mon", callback=lambda _: rumps.quit_application()))

    def _run_now(self, _=None):
        if self._running:
            return
        thread = threading.Thread(target=self._do_run, daemon=True)
        thread.start()

    def _do_run(self):
        self._running = True
        self._start_spinner()

        config = load_config()
        folders = list_folders()
        total_renamed = 0
        total_errors = 0

        for folder in folders:
            result = normalize_folder(
                root=Path(folder),
                exclude_patterns=config.get("exclude_patterns"),
                dry_run=False,
            )
            total_renamed += result.renamed
            total_errors += result.errors

        now = datetime.now().strftime("%H:%M")
        if total_errors:
            self._last_result = f"⚠️  {now} | 변환 {total_renamed}개 | 에러 {total_errors}개"
        else:
            self._last_result = f"✅  {now} | 변환 {total_renamed}개"

        self._stop_spinner()
        self._running = False
        self.title = ""
        self._build_menu()
        self._schedule_next()

    def _start_spinner(self):
        self._spinner_idx = 0
        self._tick_spinner()

    def _tick_spinner(self):
        if not self._running:
            return
        self.title = self._spinner_frames[self._spinner_idx % len(self._spinner_frames)]
        self._spinner_idx += 1
        self._spinner_timer = threading.Timer(0.1, self._tick_spinner)
        self._spinner_timer.daemon = True
        self._spinner_timer.start()

    def _stop_spinner(self):
        if self._spinner_timer:
            self._spinner_timer.cancel()
        self.title = ""

    def _add_folder(self, _):
        subprocess.run(["osascript", "-e",
            'tell application "System Events" to set frontmost of process "Python" to true'
        ])
        script = '''
        tell application "Finder"
            activate
            set folderPath to POSIX path of (choose folder with prompt "추가할 폴더를 선택해줘요")
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True,
                encoding="utf-8",
                timeout=60
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                ok, msg = add_folder(path)
                if ok:
                    self._build_menu()
                else:
                    rumps.alert(title="추가 실패", message=msg)
        except Exception as e:
            rumps.alert(title="예외", message=str(e))
            
    def _make_remove_callback(self, folder_path: str):
        def callback(_):
            name = Path(folder_path).name
            response = rumps.alert(
                title="폴더 제거",
                message=f"'{name}' 를 목록에서 제거할까요?",
                ok="제거",
                cancel="취소",
            )
            if response == 1:
                remove_folder(folder_path)
                self._build_menu()
        return callback

    def _make_interval_callback(self, seconds: int):
        def callback(_):
            config = load_config()
            config["interval"] = seconds
            save_config(config)
            if self._timer:
                self._timer.cancel()
            if seconds > 0:
                self._schedule_next()
            self._build_menu()
        return callback

    def _schedule_next(self):
        config = load_config()
        interval = config.get("interval", 1800)
        if interval <= 0:
            return
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(interval, self._run_now)
        self._timer.daemon = True
        self._timer.start()


def main():
    app = JasoMonApp()
    app._schedule_next()
    app.run()


if __name__ == "__main__":
    main()