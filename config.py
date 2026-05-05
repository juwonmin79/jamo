# ~/.jaso/config.py
# 설정 파일 관리 — config.json 읽기/쓰기 + 폴더 목록 관리

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("jaso.config")

# ─────────────────────────────────────────
# 경로 상수
# ─────────────────────────────────────────
JASO_DIR   = Path.home() / ".jaso"
CONFIG_PATH = JASO_DIR / "config.json"
LOG_DIR     = JASO_DIR / "log"

# ─────────────────────────────────────────
# 기본 설정값
# ─────────────────────────────────────────
DEFAULT_CONFIG = {
    "folders": [],
    "exclude_patterns": [
        ".git",
        ".DS_Store",
        "node_modules",
        ".venv",
        "~$*",
        "*.tmp",
        ".dropbox",
        "desktop.ini",
    ],
    "log_dir": str(LOG_DIR),
}


# ─────────────────────────────────────────
# 읽기 / 쓰기
# ─────────────────────────────────────────
def load_config() -> dict:
    """
    config.json을 읽어 dict로 반환.
    파일이 없으면 기본값으로 새로 만들고 반환.
    """
    JASO_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        logger.info(f"설정 파일 최초 생성: {CONFIG_PATH}")
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 혹시 키가 빠져 있으면 기본값으로 채워줌 (버전 업 대비)
        for key, val in DEFAULT_CONFIG.items():
            data.setdefault(key, val)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"config.json 파싱 실패: {e} — 기본값으로 초기화")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """dict를 config.json에 저장"""
    JASO_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# 폴더 관리
# ─────────────────────────────────────────
def _resolve(path_str: str) -> str:
    """~ 확장 + 절대경로 정규화 → 문자열로 반환"""
    return str(Path(path_str.rstrip("/")).expanduser().resolve())


def list_folders() -> List[str]:
    """등록된 폴더 목록 반환 (절대경로)"""
    config = load_config()
    return [_resolve(p) for p in config["folders"]]


def add_folder(path_str: str) -> tuple[bool, str]:
    """
    폴더 추가.
    반환: (성공 여부, 메시지)
    """
    resolved = _resolve(path_str)
    target = Path(resolved)

    if not target.exists():
        return False, f"경로가 존재하지 않아요: {resolved}"
    if not target.is_dir():
        return False, f"폴더가 아니에요: {resolved}"

    config = load_config()
    existing = [_resolve(p) for p in config["folders"]]

    if resolved in existing:
        return False, f"이미 등록된 폴더예요: {resolved}"

    config["folders"].append(resolved)
    save_config(config)
    return True, f"추가됨: {resolved}"


def remove_folder(path_str: str) -> tuple[bool, str]:
    """
    폴더 제거.
    반환: (성공 여부, 메시지)
    """
    resolved = _resolve(path_str)
    config = load_config()
    existing = [_resolve(p) for p in config["folders"]]

    if resolved not in existing:
        return False, f"등록되지 않은 폴더예요: {resolved}"

    config["folders"] = [p for p in config["folders"] if _resolve(p) != resolved]
    save_config(config)
    return True, f"제거됨: {resolved}"