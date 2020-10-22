#!/usr/bin/env python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Setup configuration."""

import glob
import os
import pathlib
import typing

from clif import extension
import setuptools


def _find_clif_modules() -> typing.Iterable[extension.CLIFExtension]:
  """Build list of CLIFExtensions based on CLIF-generated sources under cwd.

  Returns:
    list of CLIF extensions for setuptools.setup's ext_modules arg
  """
  modules = []
  for clif_init in glob.glob('**/*_init.cc', recursive=True):
    module_dir = pathlib.Path(clif_init).parts[0]
    module_name = clif_init.replace('/', '.').replace('_init.cc', '')
    clif_sources = [
        # CLIF-generated sources (module.cc, module_init.cc)
        clif_init.replace('_init', ''),
        clif_init,
    ]

    libraries = []
    for lib in glob.glob(os.path.join(module_dir, 'lib*.a')):
      lib = pathlib.Path(lib).stem.replace('lib', '', 1)
      libraries.append(lib)

    clif_extension = extension.CLIFExtension(
        module_name, clif_sources, include_dirs=['./'],
        libraries=libraries,
        library_dirs=[module_dir],
        extra_compile_args=['-std=c++17'])

    modules.append(clif_extension)
  return modules


setuptools.setup(
    name='pyclif_examples',
    version='1.0',
    description='Python CLIF examples',
    url='https://github.com/google/clif',
    author='CLIF authors',
    author_email='pyclif@googlegroups.com',
    ext_modules=_find_clif_modules(),
)
