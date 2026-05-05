from setuptools import setup

APP = ['menubar.py']
DATA_FILES = [
    ('', ['jaso_menubar.png']),   # ← 이 줄 수정
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'jamo.icns',
        'plist': {
        'LSUIElement': True,
        'CFBundleName': 'Jamo',
        'CFBundleDisplayName': 'Jamo',
        'CFBundleIdentifier': 'com.jake.jamo',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSDesktopFolderUsageDescription': 'Jamo가 파일명을 정규화합니다.',
        'NSDownloadsFolderUsageDescription': 'Jamo가 파일명을 정규화합니다.',
        'NSDocumentsFolderUsageDescription': 'Jamo가 파일명을 정규화합니다.',
        'NSRemovableVolumesUsageDescription': 'Jamo가 파일명을 정규화합니다.',
        'NSAppleEventsUsageDescription': 'Jamo가 Finder를 제어합니다.',
    },
    'packages': ['rumps'],
    'includes': ['normalizer', 'config'],
}
setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
