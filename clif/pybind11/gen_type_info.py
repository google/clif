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
from typing import Generator, Set

from clif.pybind11 import utils


I = utils.I


@dataclasses.dataclass
class BaseType:
  """Wraps a C++ Type."""
  cpp_name: str
  py_name: str
  cpp_namespace: str

  def generate_clif_use(self) -> Generator[str, None, None]:
    yield f'// CLIF use `{self.cpp_name}` as {self.py_name}, Pybind11Ignore'

  def generate_header(self) -> Generator[str, None, None]:
    yield from self.generate_clif_use()

  def generate_converters(self) -> Generator[str, None, None]:
    yield from ()

  def generate_type_caster(self) -> Generator[str, None, None]:
    yield from ()


@dataclasses.dataclass
class ClassType(BaseType):
  """Wraps a C++ Class."""

  module_path: str
  cpp_has_public_dtor: bool
  cpp_copyable: bool
  cpp_movable: bool
  override_in_python: bool
  enable_instance_dict: bool

  py_bases: Set[str]

  def generate_type_trait(self, type_trait: str) -> Generator[str, None, None]:
    yield ''
    yield 'namespace pybind11 {'
    yield 'namespace detail {'
    yield ''
    yield 'template <>'
    yield f'struct {type_trait}<{self.cpp_name}>: std::false_type {{}};'
    yield ''
    yield '}  // namespace detail'
    yield '}  // namespace pybind11'
    yield ''

  def generate_type_caster(self) -> Generator[str, None, None]:
    # Work around potential name collisions in
    # `PYBIND11_SMART_HOLDER_TYPE_CASTERS()` invocation, e.g. a collision
    # between a `std::tuple` alias in the global namespace (to work around
    # b/118736768) and `pybind11::tuple`.
    if self.module_path:
      py_name_fq = '.'.join([self.module_path, self.py_name])
    else:
      py_name_fq = self.py_name
    using_name = f'PyCLIF_py_name_{py_name_fq}'.replace('.', '_')
    yield f'using {using_name} = {self.cpp_name};'
    yield f'PYBIND11_SMART_HOLDER_TYPE_CASTERS({using_name})'
    if not self.cpp_copyable:
      yield from self.generate_type_trait('is_copy_constructible')
    if not self.cpp_movable:
      yield from self.generate_type_trait('is_move_constructible')

  def generate_header(self) -> Generator[str, None, None]:
    yield ''
    yield from self.generate_clif_use()
    if not self.override_in_python:
      yield f'PyObject* Clif_PyObjFrom({self.cpp_name}*, ::clif::py::PostConv);'
      yield (f'PyObject* Clif_PyObjFrom(std::shared_ptr<{self.cpp_name}>,'
             '::clif::py::PostConv);')
      if self.cpp_has_public_dtor:
        yield (f'PyObject* Clif_PyObjFrom(std::unique_ptr<{self.cpp_name}>,'
               '::clif::py::PostConv);')
        if self.cpp_movable:
          yield (f'PyObject* Clif_PyObjFrom({self.cpp_name}&&, '
                 '::clif::py::PostConv);')
      if self.cpp_copyable:
        yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}&, '
               '::clif::py::PostConv);')
        yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}*, '
               '::clif::py::PostConv);')
    yield ''
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}** output);'
    yield ('bool Clif_PyObjAs(PyObject* input, '
           f'std::shared_ptr<{self.cpp_name}>* output);')
    if self.cpp_has_public_dtor:
      yield ('bool Clif_PyObjAs(PyObject* input, '
             f'std::unique_ptr<{self.cpp_name}>* output);')
    if self.cpp_copyable and not self.override_in_python:
      yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output);'

  def generate_converters(self) -> Generator[str, None, None]:
    yield ''
    if not self.override_in_python:
      yield (f'PyObject* Clif_PyObjFrom({self.cpp_name}* c, '
             '::clif::py::PostConv) {')
      yield I + 'return pybind11::cast(c).release().ptr();'
      yield '}'
      yield ''
      yield (f'PyObject* Clif_PyObjFrom(std::shared_ptr<{self.cpp_name}> c, '
             '::clif::py::PostConv) {')
      yield I + 'return pybind11::cast(std::move(c)).release().ptr();'
      yield '}'
      yield ''
      if self.cpp_has_public_dtor:
        yield (f'PyObject* Clif_PyObjFrom(std::unique_ptr<{self.cpp_name}> c, '
               '::clif::py::PostConv) {')
        yield I + 'return pybind11::cast(std::move(c)).release().ptr();'
        yield '}'
        yield ''
        if self.cpp_movable:
          yield (f'PyObject* Clif_PyObjFrom({self.cpp_name}&& c, '
                 '::clif::py::PostConv) {')
          yield I + 'return pybind11::cast(std::move(c)).release().ptr();'
          yield '}'
          yield ''
      if self.cpp_copyable:
        yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}& c, '
               '::clif::py::PostConv) {')
        yield I + 'return pybind11::cast(c).release().ptr();'
        yield '}'
        yield ''
        yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}* c, '
               '::clif::py::PostConv) {')
        yield I + 'return pybind11::cast(c).release().ptr();'
        yield '}'
        yield ''
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}** output) {{'
    yield I + 'try {'
    yield I + I + (f'*output = pybind11::cast<{self.cpp_name}*>'
                   '(pybind11::handle(input));')
    yield I + '} catch (pybind11::cast_error) {'
    yield I + I + 'return false;'
    yield I + '}'
    yield I + 'return true;'
    yield '}'
    yield ''
    yield ('bool Clif_PyObjAs(PyObject* input, '
           f'std::shared_ptr<{self.cpp_name}>* output) {{')
    yield I + 'try {'
    yield I + I + (f'*output = pybind11::cast<std::shared_ptr<{self.cpp_name}>>'
                   '(pybind11::handle(input));')
    yield I + '} catch (pybind11::cast_error) {'
    yield I + I + 'return false;'
    yield I + '}'
    yield I + 'return true;'
    yield '}'
    yield ''
    if self.cpp_has_public_dtor:
      yield ('bool Clif_PyObjAs(PyObject* input, '
             f'std::unique_ptr<{self.cpp_name}>* output) {{')
      yield I + 'try {'
      yield I + I + ('*output = pybind11::cast<std::unique_ptr'
                     f'<{self.cpp_name}>>(pybind11::handle(input));')
      yield I + '} catch (pybind11::cast_error) {'
      yield I + I + 'return false;'
      yield I + '}'
      yield I + 'return true;'
      yield '}'
      yield ''
    if self.cpp_copyable and not self.override_in_python:
      yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output) {{'
      yield I + 'try {'
      yield I + I + (f'{self.cpp_name} output_ = pybind11::cast<'
                     f'{self.cpp_name}>(pybind11::handle(input));')
      yield I + I + '*output = output_;'
      yield I + '} catch (pybind11::cast_error) {'
      yield I + I + 'return false;'
      yield I + '}'
      yield I + 'return true;'
      yield '}'


@dataclasses.dataclass
class EnumType(BaseType):
  """Wraps a C++ Enum."""

  def generate_header(self) -> Generator[str, None, None]:
    yield ''
    yield from self.generate_clif_use()
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}&, '
           '::clif::py::PostConv);')
    yield ''
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output);'

  def generate_converters(self) -> Generator[str, None, None]:
    yield ''
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}& c, '
           '::clif::py::PostConv) {')
    yield I + 'return pybind11::cast(c).release().ptr();'
    yield '}'
    yield ''
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output) {{'
    yield I + 'try {'
    yield I + I + (f'*output = pybind11::cast<{self.cpp_name}>'
                   '(pybind11::handle(input));')
    yield I + '} catch (pybind11::cast_error) {'
    yield I + I + 'return false;'
    yield I + '}'
    yield I + 'return true;'
    yield '}'


@dataclasses.dataclass
class CapsuleType(BaseType):
  """Wraps a C++ pointer as Python capsule."""

  def generate_clif_use(self) -> Generator[str, None, None]:
    yield (f'// CLIF use `{self.cpp_name}` as {self.py_name}, '
           'PythonCapsule, Pybind11Ignore')


@dataclasses.dataclass
class ProtoType(BaseType):
  """Wraps a C++ proto Message."""

  def generate_header(self) -> Generator[str, None, None]:
    yield ''
    yield from self.generate_clif_use()
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}&, '
           '::clif::py::PostConv);')
    yield (f'PyObject* Clif_PyObjFrom(std::shared_ptr<const {self.cpp_name}>,'
           '::clif::py::PostConv);')
    yield (f'PyObject* Clif_PyObjFrom(std::unique_ptr<const {self.cpp_name}>,'
           '::clif::py::PostConv);')
    yield ''
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output);'
    yield ('bool Clif_PyObjAs(PyObject* input, '
           f'std::unique_ptr<{self.cpp_name}>* output);')

  def generate_converters(self) -> Generator[str, None, None]:
    yield ''
    yield (f'PyObject* Clif_PyObjFrom(const {self.cpp_name}& c, '
           '::clif::py::PostConv) {')
    yield I + 'return pybind11::cast(c).release().ptr();'
    yield '}'
    yield (f'PyObject* Clif_PyObjFrom(std::shared_ptr<const {self.cpp_name}> c'
           ', ::clif::py::PostConv) {')
    yield I + 'return pybind11::cast(std::move(c)).release().ptr();'
    yield '}'
    yield ''
    yield (f'PyObject* Clif_PyObjFrom(std::unique_ptr<const {self.cpp_name}> c'
           ', ::clif::py::PostConv) {')
    yield I + 'return pybind11::cast(std::move(c)).release().ptr();'
    yield '}'
    yield ''
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output) {{'
    yield I + 'try {'
    yield I + I + (f'*output = pybind11::cast<{self.cpp_name}>'
                   '(pybind11::handle(input));')
    yield I + '} catch (pybind11::cast_error) {'
    yield I + I + 'return false;'
    yield I + '}'
    yield I + 'return true;'
    yield '}'
    yield ''
    yield ('bool Clif_PyObjAs(PyObject* input, '
           f'std::unique_ptr<{self.cpp_name}>* output) {{')
    yield I + 'try {'
    yield I + I + ('*output = pybind11::cast<std::unique_ptr'
                   f'<{self.cpp_name}>>(pybind11::handle(input));')
    yield I + '} catch (pybind11::cast_error) {'
    yield I + I + 'return false;'
    yield I + '}'
    yield I + 'return true;'
    yield '}'
    yield ''


@dataclasses.dataclass
class ProtoEnumType(BaseType):
  """Wraps a C++ proto Enum."""

  def generate_header(self) -> Generator[str, None, None]:
    yield ''
    yield from self.generate_clif_use()
    yield f'PyObject* Clif_PyObjFrom({self.cpp_name}, ::clif::py::PostConv);'
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output);'

  def generate_converters(self) -> Generator[str, None, None]:
    yield ''
    yield (f'PyObject* Clif_PyObjFrom({self.cpp_name} c, '
           '::clif::py::PostConv) {')
    yield I + 'return pybind11::cast(c).release().ptr();'
    yield '}'
    yield f'bool Clif_PyObjAs(PyObject* input, {self.cpp_name}* output) {{'
    yield I + 'try {'
    yield I + I + (f'*output = pybind11::cast<{self.cpp_name}>'
                   '(pybind11::handle(input));')
    yield I + '} catch (pybind11::cast_error) {'
    yield I + I + 'return false;'
    yield I + '}'
    yield I + 'return true;'
    yield '}'
