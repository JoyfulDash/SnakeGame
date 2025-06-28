from setuptools import setup

APP = ['gameSnake.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['pygame', 'requests'],  # add requests here
    # 'iconfile': 'icon.icns',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
