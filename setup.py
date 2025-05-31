from setuptools import setup

APP = ['gamesnake.py']
DATA_FILES = ['background.wav', 'death.wav', 'eat.wav']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pygame'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
