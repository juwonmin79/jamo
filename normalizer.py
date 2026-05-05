# ~/.jaso/normalizer.py
# 코어 엔진 — CLI/launchd/메뉴바 어디서든 import해서 쓸 수 있는 순수 함수 모음

from __future__ import annotations  # Python 3.9 type hint 호환

import unicodedata
import fnmatch
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional


# ─────────────────────────────────────────
# 기본 제외 패턴
# ─────────────────────────────────────────
DEFAULT_EXCLUDE: List[str] = [
    ".git",
    ".DS_Store",
    "node_modules",
    ".venv",
    "~$*",       # Office 임시파일
    "*.tmp",
    ".dropbox",
    "desktop.ini",
]


# ─────────────────────────────────────────
# 결과 담는 그릇
# ─────────────────────────────────────────
@dataclass
class NormalizeResult:
    scanned: int = 0
    renamed: int = 0
    skipped_collision: int = 0
    skipped_excluded: int = 0
    errors: int = 0
    dry_run: bool = False
    changes: List[tuple] = field(default_factory=list)      # (old_path, new_path)
    collisions: List[tuple] = field(default_factory=list)   # (nfd_path, nfc_path)
    error_list: List[tuple] = field(default_factory=list)   # (path, error_msg)

    def summary(self) -> str:
        mode = "[DRY-RUN] " if self.dry_run else ""
        return (
            f"{mode}스캔 {self.scanned}개 | "
            f"변환 {self.renamed}개 | "
            f"충돌 건너뜀 {self.skipped_collision}개 | "
            f"제외 {self.skipped_excluded}개 | "
            f"에러 {self.errors}개"
        )


# ─────────────────────────────────────────
# 유틸 함수
# ─────────────────────────────────────────
def is_nfd(name: str) -> bool:
    """파일명이 NFD(자소분리)인지 확인"""
    return unicodedata.normalize("NFC", name) != name


def to_nfc(name: str) -> str:
    """NFD → NFC 변환"""
    return unicodedata.normalize("NFC", name)


def is_excluded(path: Path, patterns: List[str]) -> bool:
    """제외 패턴에 매칭되는지 확인 (glob 패턴 지원)"""
    name = path.name
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


# ─────────────────────────────────────────
# 핵심 함수
# ─────────────────────────────────────────
def normalize_folder(
    root: Path,
    exclude_patterns: Optional[List[str]] = None,
    dry_run: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
    logger: Optional[logging.Logger] = None,
) -> NormalizeResult:
    """
    root 폴더 아래의 모든 NFD 파일/폴더명을 NFC로 변환한다.

    동작 순서 (bottom-up):
      1. os.walk(topdown=False) → 깊은 곳부터 탐색
      2. 각 경로에서 파일 먼저 rename → 그 다음 디렉터리 rename
      3. 제외 패턴, NFC/NFD 충돌, 에러 처리
    """
    if exclude_patterns is None:
        exclude_patterns = DEFAULT_EXCLUDE

    if logger is None:
        logger = logging.getLogger("jaso.normalizer")

    result = NormalizeResult(dry_run=dry_run)
    root = root.expanduser().resolve()

    if not root.exists():
        logger.error(f"경로가 존재하지 않음: {root}")
        return result

    # ── bottom-up 탐색 ──────────────────────
    # topdown=False 이면 os.walk가 깊은 폴더부터 yield
    for dirpath, dirnames, filenames in os.walk(root, topdown=False, onerror=_walk_error_handler(result, logger)):

        current_dir = Path(dirpath)

        # ── 현재 디렉터리 자체가 제외 대상이면 스킵 ──
        if is_excluded(current_dir, exclude_patterns):
            result.skipped_excluded += 1
            continue

        # ── 1) 파일 먼저 처리 ──────────────────
        for filename in filenames:
            file_path = current_dir / filename
            result.scanned += 1

            if is_excluded(file_path, exclude_patterns):
                result.skipped_excluded += 1
                logger.debug(f"제외: {file_path}")
                continue

            if not is_nfd(filename):
                continue  # NFC면 건드릴 필요 없음

            nfc_name = to_nfc(filename)
            nfc_path = current_dir / nfc_name

            # 충돌 감지: NFC 파일이 이미 존재하면 절대 덮어쓰지 않음
            # if nfc_path.exists() and nfc_path != file_path:
            if nfc_path.exists() and not os.path.samefile(file_path, nfc_path):
                logger.warning(f"⚠️ 충돌: {file_path.name!r} → {nfc_name!r} 이미 존재")
                result.skipped_collision += 1
                result.collisions.append((file_path, nfc_path))
                if progress_callback:
                    progress_callback(f"[충돌] {file_path}")
                continue

            _do_rename(file_path, nfc_path, result, dry_run, logger, progress_callback)

        # ── 2) 하위 디렉터리 처리 (bottom-up이므로 이미 내부는 처리 완료) ──
        for dirname in dirnames:
            dir_path = current_dir / dirname
            result.scanned += 1

            if is_excluded(dir_path, exclude_patterns):
                result.skipped_excluded += 1
                continue

            if not is_nfd(dirname):
                continue

            nfc_name = to_nfc(dirname)
            nfc_path = current_dir / nfc_name

            #if nfc_path.exists() and nfc_path != dir_path:
            if nfc_path.exists() and not os.path.samefile(dir_path, nfc_path):
                logger.warning(f"⚠️ 충돌(폴더): {dir_path.name!r} → {nfc_name!r} 이미 존재")
                result.skipped_collision += 1
                result.collisions.append((dir_path, nfc_path))
                continue

            _do_rename(dir_path, nfc_path, result, dry_run, logger, progress_callback)

    return result


# ─────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────
def _do_rename(
    src: Path,
    dst: Path,
    result: NormalizeResult,
    dry_run: bool,
    logger: logging.Logger,
    progress_callback: Optional[Callable],
) -> None:
    """실제 rename 수행 (dry_run이면 로그만)"""
    try:
        if dry_run:
            logger.info(f"[DRY] {src.name!r} → {dst.name!r}  ({src.parent})")
        else:
            src.rename(dst)
            logger.info(f"✅ {src.name!r} → {dst.name!r}  ({src.parent})")

        result.renamed += 1
        result.changes.append((src, dst))

        if progress_callback:
            prefix = "[DRY] " if dry_run else ""
            progress_callback(f"{prefix}{src.name} → {dst.name}")

    except PermissionError as e:
        logger.error(f"❌ 권한 에러: {src} — {e}")
        result.errors += 1
        result.error_list.append((src, str(e)))

    except OSError as e:
        logger.error(f"❌ OS 에러: {src} — {e}")
        result.errors += 1
        result.error_list.append((src, str(e)))


def _walk_error_handler(result: NormalizeResult, logger: logging.Logger):
    """os.walk onerror 핸들러 — 접근 불가 폴더를 만나도 죽지 않음"""
    def handler(err: OSError):
        logger.warning(f"⚠️ 탐색 불가: {err.filename} — {err}")
        result.errors += 1
        result.error_list.append((err.filename, str(err)))
    return handler