from setuptools import setup
import os

APP = ['gameSnake.py']
DATA_FILES = [
    ('', ['eat.wav', 'death.wav', 'background.wav', 'highscore.wav'])  # Add all required assets here
]
OPTIONS = {
    'argv_emulation': False,
    'packages': ['pygame', 'requests', 'charset_normalizer'],
    'semi_standalone': True,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
