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
        'CFBundleName': 'Zen Macro',
        'NSScreenCaptureUsageDescription': 'This app requires screen recording access.',
        'NSAccessibilityUsageDescription': 'This app requires accessibility access.',
    }
}

setup(
    app=APP,
    name='Zen Macro',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
