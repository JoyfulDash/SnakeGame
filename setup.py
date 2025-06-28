from setuptools import setup

APP = ['snake.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pygame'],
    #'iconfile': 'icon.icns',  # Optional: Add your own icon
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
