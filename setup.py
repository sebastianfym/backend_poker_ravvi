#!/usr/bin/python3

import os
from datetime import datetime
import setuptools
import packaging.version

BASEDIR = os.path.dirname(__file__)

DATE = datetime.now().date()
VERSION = f"{DATE.year}.{DATE.month}.{DATE.day}"
if os.getenv("CI"):
    branch = os.getenv("CI_COMMIT_REF_NAME")
    CI_JOB_ID = os.getenv("CI_JOB_ID")
    if branch != "master":
        VERSION += f".dev{CI_JOB_ID}"
    else:
        VERSION += f".{CI_JOB_ID}"
else:
    VERSION += ".dev0"
VERSION = str(packaging.version.parse(VERSION))

with open(os.path.join(BASEDIR, "ravvi_poker", "build.py"), "w") as f:
    f.write(f'__version__ = "{VERSION}"\n')


setuptools.setup(
    name="ravvi-poker",
    version=VERSION,
    author="Alexander Keda",
    author_email="alexander.keda@ravvi.net",
    description="Ravvi Poker",
    packages=setuptools.find_packages(),
    # fmt: off
    package_data={
        "ravvi_poker.db.schema": ["*.sql"],
        "ravvi_poker.db.deploy": ["*.sql"],
    },
    entry_points={
        "console_scripts": [
            "ravvi_poker_db=ravvi_poker.db.cli:main",
            "ravvi_poker_api=ravvi_poker.api.cli:main",
        ]
    },
    #data_files=[],
    install_requires=[
        "psycopg",
        "fastapi",
        "python-multipart",
        "passlib",
        "PyJWT",
        "PyYAML",
        "uvicorn",
        "gunicorn",
        "websockets",
        "pydantic[email]",
    ],
    extras_require={
        "tests": [
            "coverage",
            "pytest",
            "pytest-cov",
            "pytest-asyncio",
            "httpx"
        ]
    },
    # fmt: on
)
