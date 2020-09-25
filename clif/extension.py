# Copyright 2020 Google LLC
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
"""CLIF setuptools utility functions.

Example Usage:

  from clif import extension
  import setuptools

  setuptools.setup(
    ...
    extensions=[
      extension.CLIFExtension('foo',
        ['foo.cc', 'foo_init.cc'],
        include_dirs=['mydir'],
        libraries=['myutils'],
        ...
      )
    ]
  )
"""

import os
import sysconfig

import setuptools


_CLIF_DIR = os.path.dirname(__file__)

_CLIF_LIBRARIES = [
    'absl_bad_optional_access',
    'absl_raw_logging_internal',
    'absl_log_severity',
    'glog',
    'protobuf',
]

_CLIF_INCLUDE_DIRS = [
    # Path to python header
    sysconfig.get_path('include'),
    # Path to CLIF runtime headers
    os.path.dirname(_CLIF_DIR),
]

_CLIF_SOURCES = [
    os.path.join(_CLIF_DIR, 'python', relpath)
    for relpath in ['pyproto.cc', 'runtime.cc', 'slots.cc', 'types.cc']
]


class CLIFExtension(setuptools.Extension):
  """Extends setuptools.Extension to provide CLIF sources, includes and libs."""

  def __init__(self, name, sources, *args, **kwargs):
    kwargs['libraries'] = kwargs.get('libraries', []) + _CLIF_LIBRARIES
    kwargs['include_dirs'] = kwargs.get('include_dirs', []) + _CLIF_INCLUDE_DIRS
    sources += _CLIF_SOURCES
    super(CLIFExtension, self).__init__(name, sources, *args, **kwargs)

