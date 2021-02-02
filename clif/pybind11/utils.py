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

"""Utility functions for pybind11 code generator."""

# Use two spaces indentation for generated code.
I = '  '


def find_operator(s, prefix='::operator'):
  """Use to find the operator in a cpp_name string."""
  index = s.find(prefix)
  if index < 0:
    return -1
  index += len(prefix)
  c = s[index:index + 1]
  if not c or c == '_' or c.isalnum():
    return -1
  return index


def is_dunder_name(s):
  return s.startswith('__') and s.endswith('__')
