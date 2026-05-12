from setuptools import setup

APP = ['menubar.py']
DATA_FILES = [
    ('', ['jaso_menubar.png']),   # ← 이 줄 수정
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'jaso-mon.icns',
        'plist': {
        'LSUIElement': True,
        'CFBundleName': 'Jaso-Mon',
        'CFBundleDisplayName': 'Jaso-Mon',
        'CFBundleIdentifier': 'com.jake.jaso-mon',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'NSDesktopFolderUsageDescription': 'Jaso-Mon이 파일명을 정규화합니다.',
        'NSDownloadsFolderUsageDescription': 'Jaso-Mon이 파일명을 정규화합니다.',
        'NSDocumentsFolderUsageDescription': 'Jaso-Mon이 파일명을 정규화합니다.',
        'NSRemovableVolumesUsageDescription': 'Jaso-Mon이 파일명을 정규화합니다.',
        'NSAppleEventsUsageDescription': 'Jaso-Mon이 Finder를 제어합니다.',
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
