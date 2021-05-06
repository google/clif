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


def is_nested_template(s: str) -> bool:
  # This function works around CLIF matcher bug b/118736768:
  # cpp_exact_type is incorrect for nested templates.
  # This is a crude stop-gap way of unblocking development
  # work for now.
  return '>>' in s


def is_usable_cpp_exact_type(s: str) -> bool:
  return not is_nested_template(s) or '&' in s
