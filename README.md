# Jamo (자모)

macOS에서 한글 파일명의 자소분리(NFD)를 NFC로 일괄 정규화하는 도구.

OneDrive 동기화, Outlook 첨부파일 저장 시 발생하는 한글 깨짐 문제를 해결합니다.

## 기능

- 메뉴바 앱 — 주기적 자동 실행 (1분~6시간)
- CLI — `jaso run` 한 방에 정규화
- Finder Quick Action — 폴더 우클릭 → 자소 변환
- NFC/NFD 충돌 감지 — 안전한 변환
- dry-run 모드 — 미리보기
- 로그 기록 — `~/.jaso/log/`

## 설치

### 요구사항
- macOS 12+
- Python 3.9+

### 설치 방법

```bash
# 저장소 클론
git clone https://github.com/juwonmin79/jamo.git
cd jamo

# 의존성 설치
python3 -m pip install rumps tqdm py2app

# 앱 빌드
python3 setup.py py2app

# 설치
cp -r dist/Jamo.app /Applications/
open /Applications/Jamo.app
```

### CLI 설치

```bash
sudo cp cli.py /usr/local/bin/jaso
sudo chmod +x /usr/local/bin/jaso
```

## 사용법

```bash
jaso add ~/Downloads          # 폴더 등록
jaso add ~/Library/CloudStorage/OneDrive-xxx/문서
jaso list                     # 등록 폴더 확인
jaso run --dry                # 미리보기
jaso run                      # 실제 변환
```

## 라이선스

MIT
