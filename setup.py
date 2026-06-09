from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='HITPanDownload',
    version='0.1.0',
    py_modules=['main', 'net', 'parser'],
    install_requires=required,
    entry_points={
        'console_scripts': [
            'hitpandownload=main:main',
        ],
    },
)
