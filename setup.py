from setuptools import setup
import os

APP = ['gameSnake.py']
DATA_FILES = [
    ('', ['eat.wav', 'death.wav', 'background.wav', 'highscore.wav'])  # Add all required assets here
]
OPTIONS = {
    'argv_emulation': False,
    'packages': ['pygame', 'requests'],
    'includes': ['charset_normalizer'],  # fix requests warning
    'resources': ['eat.wav', 'background.wav', 'death.wav', 'highscore.wav'],
    'semi_standalone': True,
}


setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
