from setuptools import setup

APP = ['gameSnake.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pygame'],
    'semi_standalone': True,  # Added this option
    # 'iconfile': 'icon.icns',  # Optional: Add your own icon
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
