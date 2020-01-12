#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ["telnetlib3==1.0.2", ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', "pytest-asyncio>=0.10", ]

setup(
    author="Rob van der Most",
    author_email='silvester747@gmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="AsyncIO access to Marantz AVRs.",
    entry_points={
        'console_scripts': [
            'aio_marantz_avr=aio_marantz_avr.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='aio_marantz_avr',
    name='aio_marantz_avr',
    packages=find_packages(include=['aio_marantz_avr', 'aio_marantz_avr.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/silvester747/aio_marantz_avr',
    version='0.1.0',
    zip_safe=False,
)
