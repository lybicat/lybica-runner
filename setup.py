from setuptools import setup

setup(
    name = 'lybica',
    version = '0.1',
    description = 'runner script for lybica',
    url = 'https://github.com/lybicat/lybica-runner',
    package_dir = {'': 'src'},
    packages = [
        'lybica',
        'lybica.actions',
        ],
    install_requires=['zipstream', 'requests'],
    platforms = 'any',
)
