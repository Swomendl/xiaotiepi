"""
setup.py - 使用 py2app 打包小铁皮为 macOS 应用
"""

import os
from setuptools import setup

APP = ['main.py']
DATA_FILES = []

# 查找 conda 库路径
CONDA_LIB = os.environ.get('CONDA_PREFIX', '/opt/homebrew/Caskroom/miniforge/base') + '/lib'

# 需要包含的动态库
FRAMEWORKS = []
for lib in ['libffi.8.dylib', 'libtk8.6.dylib', 'libtcl8.6.dylib']:
    lib_path = os.path.join(CONDA_LIB, lib)
    if os.path.exists(lib_path):
        FRAMEWORKS.append(lib_path)

OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'frameworks': FRAMEWORKS,
    'plist': {
        'CFBundleName': '小铁皮',
        'CFBundleDisplayName': '小铁皮',
        'CFBundleIdentifier': 'com.xiaotiepi.pet',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
        'NSAppTransportSecurity': {
            'NSAllowsArbitraryLoads': True,
        },
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
