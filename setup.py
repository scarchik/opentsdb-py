from setuptools import setup


setup(
    name='opentsdb-py',
    version='0.1.0',
    author='Sergey Suglobov',
    author_email='s.suglobov@gmail.com',
    py_modules=['opentsdb'],
    keywords="opentsdb, tsdb",
    url='https://github.com/scarchik/opentsdb-py',
    description='Python client for OpenTSDB',
    install_requires=[
        "setuptools",
    ],
)
