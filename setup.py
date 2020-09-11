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
  if 'wrap_protos' in d:
    examples_tree.append((d+'/protos', glob.glob(d+'/protos/*')))

setuptools.setup(
    name='pyclif',
    version='0.3',
    description='Python CLIF C++ wrapper generator',
    long_description=('Python extension module generator based on CLIF\n'
                      'framework. It uses Clang for C++ header analisys\n'
                      'and a runtime library supporting std:: type convertions.'
                      '\n'),
    url='https://github.com/google/clif',
    author='Mike Rovner and the other CLIF authors',
    author_email='pyclif@googlegroups.com',
    # Contained modules and scripts.
    packages=['clif', 'clif.protos', 'clif.python', 'clif.python.utils'],
    data_files=[
        # pylint: disable=bad-continuation
        ('python', glob.glob('clif/python/*.cc') +
                   glob.glob('clif/python/*.h') +
                   glob.glob('clif/python/*.md')),
        ] + examples_tree,
    entry_points={
        'console_scripts': [
            'pyclif = clif.pyclif:start',
            'pyclif_proto = clif.python.proto:Start',
            ],
        },
    ext_modules=[
        setuptools.Extension(
            'clif.python.utils.proto_util', [
                # proto_util cc lib
                'clif/python/proto_util.cc',
                # CLIF-generated sources for proto_util wrapper
                'clif/python/utils/proto_util.cc',
                'clif/python/utils/proto_util.init.cc',
                # 'clif_runtime',
                'clif/python/pyproto.cc',
                'clif/python/runtime.cc',
                'clif/python/slots.cc',
                'clif/python/types.cc',
                ],
            include_dirs=[
                # Path to CLIF runtime headers
                './',
                ],
            extra_compile_args=['-std=c++11'],
            libraries=['protobuf'],
            ),
        ],
    install_requires=[
        'setuptools>=18.5',
        'pyparsing>=2.2.0',
        'protobuf>=3.2',
        ],
    # PyPI package information.
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
