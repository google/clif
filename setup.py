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

from distutils import sysconfig  # pylint: disable=deprecated-module
import os
import setuptools


if not os.path.exists('clif/protos/ast_pb2.py'):
  raise RuntimeError('clif/protos/ast_pb2.py not found. See INSTALL.sh.')


setuptools.setup(
    name='pyclif',
    version='0.4',
    description='Python CLIF C++ wrapper generator',
    long_description=('Python extension module generator based on CLIF\n'
                      'framework. It uses Clang for C++ header analysis\n'
                      'and a runtime library supporting std:: type convertions.'
                      '\n'),
    url='https://github.com/google/clif',
    author='Mike Rovner and the other CLIF authors',
    author_email='pyclif@googlegroups.com',
    # Contained modules and scripts.
    packages=['clif', 'clif.protos', 'clif.python', 'clif.python.utils'],
    package_data={'clif': ['python/*.cc', 'python/*.h']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'pyclif = clif.pyclif:start',
            'pyclif_proto = clif.python.proto:Start',
        ],
    },
    ext_modules=[
        setuptools.Extension(
            'clif.python.utils.proto_util',
            [
                # proto_util cc lib
                'clif/python/proto_util.cc',
                # CLIF-generated sources for proto_util wrapper
                'clif/python/utils/proto_util.cc',
                'clif/python/utils/proto_util.init.cc',
                # CLIF runtime
                'clif/python/pickle_support.cc',
                'clif/python/pyproto.cc',
                'clif/python/runtime.cc',
                'clif/python/slots.cc',
                'clif/python/types.cc',
            ],
            include_dirs=[
                # Path to python header
                sysconfig.get_python_inc(),
                # Path to CLIF runtime headers
                './',
            ],
            extra_compile_args=['-std=c++17'],
            library_dirs=[
                sysconfig.get_python_lib()
            ],
            libraries=[
                'absl_bad_optional_access',
                'absl_raw_logging_internal',
                'absl_log_severity',
                'glog',
                'protobuf',
            ],
        ),
    ],
    python_requires='>=3.8.0',
    install_requires=[
        'setuptools>=24.2.0',
        'pyparsing==2.2.2',
        'protobuf>=3.8.0',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Code Generators',
    ],
    license='Apache 2.0',
    keywords='Google C++ extension module wrapper generator clif',
)
