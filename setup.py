"""eztest - A python package to do performance/load test

Copyright (C) 2014 lgt, version 1.0 by lgt
* https://github.com/lgt1001/eztest
"""
from setuptools import setup

setup(
    name="eztest",
    version="1.0.6",
    description="eztest is a Python package and execution used for performance/load testing.",
    long_description=open('README.rst').read(),
    author='lgt',
    author_email='lgt.1001-@163.com',
    maintainer='lgt',
    maintainer_email='lgt.1001-@163.com',
    url='https://github.com/lgt1001/eztest',
    download_url='https://github.com/lgt1001/eztest',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
    ],
    keywords='performance load test testing performance-test load-test performance-testing load-testing',
    license="GPL",
    platforms=["Windows", "MacOS", "Unix", "Linux"],
    packages=['eztest'],
    zip_safe=True,
    entry_points=dict(console_scripts=['eztest=eztest:main'])
)
