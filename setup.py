#!/usr/bin/python3

import os
from datetime import datetime
import setuptools
import packaging.version

BASEDIR = os.path.dirname(__file__)

DATE = datetime.now().date()
VERSION = f"{DATE.year}.{DATE.month}.{DATE.day}"
if os.getenv('CI'):
    branch = os.getenv('CI_COMMIT_REF_NAME')
    CI_JOB_ID = os.getenv('CI_JOB_ID')
    if branch!='master':
        VERSION += f".dev{CI_JOB_ID}"
    else:
        VERSION += f".{CI_JOB_ID}"
else:
    VERSION += '.dev0'
VERSION = str(packaging.version.parse(VERSION))

with open(os.path.join(BASEDIR, "ravvi_poker_backend", "build.py"), "w") as f:
    f.write(f'__version__ = "{VERSION}"\n')


packages=setuptools.find_packages()

setuptools.setup(
    name="ravvi-poker-backend",
    version=VERSION,
    author="Alexander Keda",
    author_email="alexander.keda@ravvi.net",
    description="Ravvi Poker Backend",
    packages=packages,
    package_data={
    },

    entry_points={
        'console_scripts': [
        #    'ravvi_pysample=ravvi_pysample.cli:main',
        ]
    },

    data_files= [
    ],

    install_requires=[
    ],
    
    cmdclass={
    },
)
