# Copyright 2021 Google LLC
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

"""Declare various types to collect information for code generation."""

import dataclasses
from typing import Generator


@dataclasses.dataclass
class BaseType:
  """Wraps a C++ Type."""
  cpp_name: str
  py_name: str
  cpp_namespace: str

  def generate_clif_use(self) -> Generator[str, None, None]:
    yield f'// CLIF use `{self.cpp_name}` as {self.py_name}'

  def generate_header(self) -> Generator[str, None, None]:
    yield from self.generate_clif_use()

  def generate_converters(self) -> Generator[str, None, None]:
    yield from ()

  def generate_type_caster(self) -> Generator[str, None, None]:
    yield from ()


@dataclasses.dataclass
class ClassType(BaseType):
  """Wraps a C++ Class."""

  def generate_type_caster(self) -> Generator[str, None, None]:
    yield f'PYBIND11_SMART_HOLDER_TYPE_CASTERS({self.cpp_name})'

  def generate_header(self) -> Generator[str, None, None]:
    yield ''
    yield from self.generate_clif_use()
    yield f'PyObject* Clif_PyObjFrom({self.cpp_name}*, ::clif::py::PostConv);'
    yield f'PyObject* Clif_PyObjFrom({self.cpp_name}&&, ::clif::py::PostConv);'
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}&, '
           '::clif::py::PostConv);')
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}*, '
           '::clif::py::PostConv);')
    yield ''

  def generate_converters(self) -> Generator[str, None, None]:
    yield ''
    yield (f'PyObject* Clif_PyObjFrom({self.cpp_name}* c, '
           '::clif::py::PostConv) {')
    yield '  return pybind11::cast(c).ptr();'
    yield '}'
    yield ''
    yield (f'PyObject* Clif_PyObjFrom({self.cpp_name}&& c, '
           '::clif::py::PostConv) {')
    yield '  return pybind11::cast(&c).ptr();'
    yield '}'
    yield ''
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}& c, '
           '::clif::py::PostConv) {')
    yield '  return pybind11::cast(&c).ptr();'
    yield '}'
    yield ''
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}* c, '
           '::clif::py::PostConv) {')
    yield '  return pybind11::cast(c).ptr();'
    yield '}'
    yield ''


@dataclasses.dataclass
class EnumType(BaseType):
  """Wraps a C++ Enum."""

  def generate_header(self) -> Generator[str, None, None]:
    yield ''
    yield from self.generate_clif_use()
    yield f'PyObject* Clif_PyObjFrom({self.cpp_name}*, ::clif::py::PostConv);'
    yield ''

  def generate_converters(self) -> Generator[str, None, None]:
    yield ''
    yield (f'PyObject* Clif_PyObjFrom({self.cpp_name}* c, '
           '::clif::py::PostConv) {')
    yield '  return pybind11::cast(c).ptr();'
    yield '}'
    yield ''
