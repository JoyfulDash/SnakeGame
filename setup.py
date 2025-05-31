from setuptools import setup

APP = ['your_game.py']
DATA_FILES = ['assets']  # or a list of specific assets
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pygame'],
    'includes': [],
    'iconfile': 'assets/icon.icns'  # Optional: path to a .icns Mac icon file
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
