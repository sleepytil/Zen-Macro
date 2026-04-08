from setuptools import setup


APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'zen.icns',
    'resources': ['images', 'sleepytil.png'],
    'excludes': ['rubicon'],
    'plist': {
        'CFBundleIdentifier': 'com.sleepytil.Zen Macro',
        'CFBundleName': 'Zen Macro'
    }
}

setup(
    app=APP,
    name='Zen Macro',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
