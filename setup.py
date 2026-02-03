"""
setup.py - 使用 py2app 打包小铁皮为 macOS 应用
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': '小铁皮',
        'CFBundleDisplayName': '小铁皮',
        'CFBundleIdentifier': 'com.xiaotiepi.pet',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
    },
    'packages': ['paper_agent', 'anthropic', 'httpx', 'httpcore', 'anyio', 'sniffio', 'certifi', 'idna', 'h11'],
    'excludes': ['setuptools', 'pkg_resources', 'wheel', 'pip'],
    'includes': ['tkinter', 'json', 'threading', 'pathlib', 'xml.etree.ElementTree'],
}

setup(
    app=APP,
    name='小铁皮',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
