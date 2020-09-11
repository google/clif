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

"""Example for using type_customization.extend."""

from typing import Any, TYPE_CHECKING

from clif.examples.extend_from_python.python import _example as ext

from clif.python import type_customization

MyClass = ext.MyClass
if TYPE_CHECKING:  # b/161575039
  MyClass = Any


@type_customization.extend(ext.MyClass)
class _(object):
  """Anonymous helper class."""

  def g(self):
    pass

  def h(self):
    return 2

  def i(self, x):
    del x
    pass

  def j(self, x):
    return 2 * x

  def k(self, x, y):
    return 2 * x + y
