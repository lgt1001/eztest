"""eztest - A python package to do performance/load test

Copyright (C) 2014 lgt, version 1.0 by lgt
* https://github.com/lgt1001/eztest
"""
from setuptools import setup, find_packages

setup(
    name="eztest",
    version="1.0.3",
    description="eztest package is used for a load test",
    long_description=open('README.rst').read(),
    author='lgt',
    author_email='lgt.1001-@163.com',
    maintainer='lgt',
    maintainer_email='lgt.1001-@163.com',
    url='https://github.com/lgt1001/eztest',
    download_url='https://github.com/lgt1001/eztest',
    #packages=['eztest'],
    #py_modules=[],
    #scripts=[],
    #ext_modules=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    keywords='test load performance',
    license="GPL",
    platforms=["Windows", "MacOS", "Unix", "Linux"],
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    zip_safe=False,
    entry_points=dict(console_scripts=['eztest=eztest:main'])
)
