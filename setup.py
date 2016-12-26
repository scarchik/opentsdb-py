from setuptools import setup, find_packages

from opentsdb import __version__


setup(
    name='opentsdb-py',
    version=__version__,
    author='Sergey Suglobov',
    author_email='s.suglobov@gmail.com',
    packages=find_packages(),
    keywords="opentsdb, tsdb",
    url='https://github.com/scarchik/opentsdb-py',
    description='Python client for OpenTSDB',
    install_requires=[
        "setuptools",
    ],
)
