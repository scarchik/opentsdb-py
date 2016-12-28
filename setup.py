from setuptools import setup, find_packages

from opentsdb import __version__


setup(
    name='opentsdb-py',
    version=__version__,
    author='Sergey Suglobov',
    author_email='s.suglobov@gmail.com',
    packages=find_packages(),
    keywords="opentsdb, tsdb, metrics",
    url='https://github.com/scarchik/opentsdb-py',
    description='Python3 client for OpenTSDB',
    install_requires=[
        "setuptools",
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
