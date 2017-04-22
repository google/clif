# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup configuration."""

import glob
import os
import platform
# pylint: disable=g-import-not-at-top
try:
  import setuptools
except ImportError:
  from ez_setup import use_setuptools
  use_setuptools()
  import setuptools

py_version = platform.python_version_tuple()
if py_version < ('2', '7') or py_version[0] == '3' and py_version < ('3', '4'):
  raise RuntimeError('Python version 2.7 or 3.4+ required')

if not os.path.exists('clif/protos/ast_pb2.py'):
  raise RuntimeError('clif/protos/ast_pb2.py not found. See INSTALL.sh.')

examples_tree = [('examples', glob.glob('examples/*.*'))]
for d in filter(os.path.isdir, glob.glob('examples/*')):
  examples_tree.append((d, glob.glob(d+'/*.*')))
  examples_tree.append((d+'/python', glob.glob(d+'/python/*')))

setuptools.setup(
    name='pyclif',
    version='0.2',
    description='Python CLIF C++ wrapper generator',
    long_description='...',
    url='https://github.com/google/clif',
    author='Mike Rovner and the other CLIF authors',
    author_email='pyclif@googlegroups.com',
    # Contained modules and scripts.
    packages=['clif', 'clif.protos', 'clif.python'],
    data_files=[
        # pylint: disable=bad-continuation
        ('python', glob.glob('clif/python/*.cc') +
                   glob.glob('clif/python/*.h') +
                   glob.glob('clif/python/*.md')),
        ] + examples_tree,
    entry_points={'console_scripts': ['pyclif = clif.pyclif:start']},
    install_requires=[
        'setuptools>=18.5',
        'pyparsing>=2.0.7',
        'protobuf>=3.2',
        ],
    # PyPI package information.
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: C++',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Code Generators',
        ],
    license='Apache 2.0',
    keywords='Google C++ extension module wrapper generator clif',
    )
