# cli.py
# jaso CLI 진입점 — argparse로 명령어 파싱 후 코어/설정 모듈 호출

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

# ── 프로젝트 루트를 path에 추가 (어디서 실행해도 import 되게) ──
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from config import (
    LOG_DIR, add_folder, list_folders,
    load_config, remove_folder,
)
from normalizer import normalize_folder


# ─────────────────────────────────────────
# 로거 셋업
# ─────────────────────────────────────────
def setup_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{date.today()}.log"

    logger = logging.getLogger("jaso")
    logger.setLevel(logging.DEBUG)

    # 파일 핸들러 (전체 기록)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    # 콘솔 핸들러 (WARNING 이상만 — tqdm과 겹치지 않게)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


# ─────────────────────────────────────────
# 명령어 핸들러
# ─────────────────────────────────────────
def cmd_list(_args) -> None:
    folders = list_folders()
    if not folders:
        print("📭 등록된 폴더가 없어요. 'jaso add <경로>'로 추가해봐요.")
        return
    print(f"📁 등록된 폴더 ({len(folders)}개):")
    for i, f in enumerate(folders, 1):
        exists = "✅" if Path(f).exists() else "❌ 경로 없음"
        print(f"  {i}. {f}  {exists}")


def cmd_add(args) -> None:
    ok, msg = add_folder(args.path)
    icon = "✅" if ok else "❌"
    print(f"{icon} {msg}")


def cmd_remove(args) -> None:
    ok, msg = remove_folder(args.path)
    icon = "✅" if ok else "❌"
    print(f"{icon} {msg}")


def cmd_run(args) -> None:
    try:
        from tqdm import tqdm
        has_tqdm = True
    except ImportError:
        has_tqdm = False

    logger = setup_logger()
    config = load_config()
    dry_run: bool = args.dry

    # ── 대상 폴더 결정 ──────────────────────
    if args.path:
        # 일회성 경로 (등록 안 해도 됨)
        targets = [Path(args.path).expanduser().resolve()]
    else:
        folders = list_folders()
        if not folders:
            print("📭 등록된 폴더가 없어요. 'jaso add <경로>'로 먼저 추가해줘요.")
            return
        targets = [Path(f) for f in folders]

    mode_label = "🔍 DRY-RUN (실제 변경 없음)" if dry_run else "🚀 변환 시작"
    print(f"\n{mode_label} — 대상 {len(targets)}개 폴더\n")

    total_result_summary = []

    for target in targets:
        print(f"📂 {target}")
        if not target.exists():
            print(f"  ❌ 경로가 존재하지 않아요. 스킵.\n")
            continue

        # ── 진행률 바 설정 ──────────────────
        if has_tqdm:
            bar = tqdm(desc="  처리중", unit="개", dynamic_ncols=True)
            def progress(msg: str, _bar=bar):
                _bar.set_postfix_str(Path(msg.split("→")[0].strip()).name[:30], refresh=True)
                _bar.update(1)
        else:
            def progress(msg: str):
                print(f"  → {msg}")

        result = normalize_folder(
            root=target,
            exclude_patterns=config.get("exclude_patterns"),
            dry_run=dry_run,
            progress_callback=progress,
            logger=logger,
        )

        if has_tqdm:
            bar.close()

        # ── 결과 출력 ──────────────────────
        print(f"  {result.summary()}")

        if result.collisions:
            print(f"\n  ⚠️  충돌 목록 (수동 확인 필요):")
            for nfd_p, nfc_p in result.collisions:
                print(f"    - NFD: {nfd_p.name}")
                print(f"      NFC: {nfc_p.name}  ← 이미 존재")

        if result.error_list:
            print(f"\n  ❌ 에러 목록:")
            for path, err in result.error_list:
                print(f"    - {path}: {err}")

        print()
        total_result_summary.append((target, result))

    # ── 전체 합산 ──────────────────────────
    if len(targets) > 1:
        total_scanned = sum(r.scanned for _, r in total_result_summary)
        total_renamed = sum(r.renamed for _, r in total_result_summary)
        total_errors  = sum(r.errors  for _, r in total_result_summary)
        print("─" * 40)
        print(f"📊 전체 합계 | 스캔 {total_scanned}개 | 변환 {total_renamed}개 | 에러 {total_errors}개")

    from config import LOG_DIR as ld
    print(f"\n📝 로그: {ld / f'{date.today()}.log'}")


# ─────────────────────────────────────────
# argparse 셋업
# ─────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jaso",
        description="한글 자소분리(NFD) → NFC 일괄 정규화 도구",
    )
    sub = parser.add_subparsers(dest="command", metavar="명령어")
    sub.required = True

    # list
    sub.add_parser("list", help="등록된 폴더 목록 보기")

    # add
    p_add = sub.add_parser("add", help="폴더 추가")
    p_add.add_argument("path", help="추가할 폴더 경로 (예: ~/Downloads)")

    # remove
    p_rm = sub.add_parser("remove", help="폴더 제거")
    p_rm.add_argument("path", help="제거할 폴더 경로")

    # run
    p_run = sub.add_parser("run", help="NFD → NFC 변환 실행")
    p_run.add_argument("path", nargs="?", default=None, help="일회성 폴더 (생략 시 등록 폴더 전체)")
    p_run.add_argument("--dry", action="store_true", help="미리보기만 (실제 변경 없음)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "list":   cmd_list,
        "add":    cmd_add,
        "remove": cmd_remove,
        "run":    cmd_run,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()