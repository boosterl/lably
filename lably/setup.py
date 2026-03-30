from setuptools import setup

APP = ['__main.py__']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': 'lably',
        'CFBundleDisplayName': 'lably',
        'CFBundleVersion': '0.0.1',
        'CFBundleShortVersionString': '0.1',
        'NSHumanReadableCopyright': 'Copyright © 2025 Bram Oosterlynck'
    },
    'packages': [],
    'includes': ['AppKit', 'Foundation'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
