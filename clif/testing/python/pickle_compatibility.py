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

"""Home for Python-side customizations."""

from clif.python import type_customization
from clif.testing.python._pickle_compatibility import *  # pylint: disable=wildcard-import


@type_customization.extend(StoreTwoUsingExtend)  # pylint: disable=undefined-variable
class _:

  def __reduce_ex__(self, protocol):
    return (self.__class__, (self.Get(0), self.Get(1)))
