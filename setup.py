# Copyright 2025 PhonePe Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from setuptools import setup, find_packages

import phonepe

CURRENT_PYTHON = sys.version_info[:2]
REQUIRED_PYTHON = (3, 0)

if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write("""
    ==========================
    Unsupported Python version
    ==========================
    This version of Requests requires at least Python {}.{}, but
    you're trying to install it on Python {}.{}. To resolve this,
    consider upgrading to a supported Python version.
    """.format(
        *(REQUIRED_PYTHON + CURRENT_PYTHON)
    )
    )
    sys.exit(1)


setup(
    name='phonepe-pg-sdk-python',
    version=phonepe.__version__,
    author='PhonePe',
    description='SDK for integration with PhonePe PG APIs',
    packages=find_packages(),
    install_requires=[
        'APScheduler <= 3.10.1',
        'dataclasses-json <= 0.5.8',
        'requests <= 2.31.0',
        'urllib3 <= 1.26.12',
    ],
)
