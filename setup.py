#!/usr/bin/env python
# -*- coding: utf-8 -*-

# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from shutil import which, copyfile
from subprocess import check_output, CalledProcessError

ARCH = 'x64'
VERSION = 3.6
PYTHONNET = 'git+https://github.com/QuantConnect/pythonnet'
PACKAGES = ['conda', 'pip', 'wheel', 'setuptools', 'pandas']
README = 'https://github.com/QuantConnect/Lean#installation-instructions'
VCForPython27 = 'https://www.microsoft.com/en-us/download/details.aspx?id=44266'
WIN32 = sys.platform == "win32" 

class PythonSupport:

    def __init__(self):
        self.print_header()
        self.check_requirements()
        self.target = self.get_target_path()
        self.conda = which('conda')

    def print_header(self):
        vc = str() if not WIN32 else f'''
        - Visual C++ for Python: {VCForPython27}'''
        print(f'''
    Python support in Lean with pythonnet
    =====================================

    Prerequisites:
        - LEAN: {README}
        - Python {VERSION} {ARCH}{vc}
        - git
        - pip

    It will update {', '.join(PACKAGES)} packages.
    ''')

    def check_requirements(self):
        version = sys.version_info.major + sys.version_info.minor / 10
        arch = "x64" if sys.maxsize > 2**32 else "x86"
        if version != VERSION or arch != ARCH :
            exit(f'Python {VERSION} {ARCH} is required: version {version} {arch} found.')

        if which('git') is None:
            exit('Git is required and not found in the path. Link to install: https://git-scm.com/downloads')

        if which('pip') is None:
            exit('pip is required and not found in the path.')

    def get_target_path(self):

        for path, dirs, files in os.walk('packages'):
            if 'Python.Runtime.dll' in files:
                path = os.path.join(path, 'Python.Runtime.dll')
                ori = path[0:-4] + '.ori'

                # Save the original file
                if not os.path.exists(ori):
                    os.rename(path, ori)
                    copyfile(ori, path)

                return path

        exit(f'Python.Runtime.dll not found in packages tree.{os.linesep}Please restore Nuget packages ({README})')

    def update_package_dll(self):
        path = os.path.dirname(sys.executable)
        file = os.path.join(path, 'Lib', 'site-packages', 'Python.Runtime.dll')

        if not os.path.exists(file):
            exit('Python.Runtime.dll not found in site-packages directories.')

        copyfile(file, self.target)

    def install(self, package):
        cmd = [self.conda, 'update', '-y', package]

        # If conda is not available or package is from git, use pip
        if package.startswith('git') or self.conda is None:
            if package == 'conda': return True
            cmd = [sys.executable, '-m', 'pip', 'install', '-U', package]

        try:
            output = check_output(cmd).decode('UTF-8')
        except CalledProcessError as e:
            output = os.linesep.join([str(x)[2:-1] for x in e.output.splitlines()])

        message = str([x for x in output.splitlines() if len(x) > 0][-1])
        success = message.find('already') > -1 or message.startswith('Successfully installed')

        # If not successfully installed or updated, pass the whole output to let the use know to do
        print(f'{package}: {message}' if success else output)
        return success


if __name__ == "__main__":

    pythonSupport = PythonSupport()

    # Installs/updates pip and wheel: required for pythonnet
    #                  pandas: requires for Lean
    print('''
    Install/updates required packages
    ---------------------------------
    ''')

    for package in PACKAGES:
        pythonSupport.install(package)

    print('''
    Install/updates pythonnet and copy the dynamic library to Lean solution
    -----------------------------------------------------------------------
    ''')

    if pythonSupport.install(PYTHONNET):
        pythonSupport.update_package_dll()
        print(f'Please REBUILD Lean solution to complete pythonnet setup.')
    elif WIN32:
        print(f'Failed to install pythonnet. Please install Visual C++ for Python: {VCForPython27}')
