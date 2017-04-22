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

"""Tests for clif.python.types."""

import textwrap
import unittest
from clif.python import pyext
from clif.python import types


class TypesTest(unittest.TestCase):

  def testClassType(self):
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'fq.py.path', w, w+'_Type', ns,
                        can_copy=False, can_destruct=True,
                        down_cast=None, virtual='')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      PyObject* Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;
    """))

  def testClassTypeWithNoDtor(self):
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'fq.py.path', w, w+'_Type', ns,
                        can_copy=False, can_destruct=False,
                        down_cast=None, virtual='')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      PyObject* Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;
    """))

  def testEnumType(self):
    t = types.EnumType('c::name::cpp_name', 'fq.py.path', 'Enum', 'clif::_Type')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name* output);
      PyObject* Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv);
    """))

  def testProtoType(self):
    t = types.ProtoType('c::cpp_name', 'fq.py.path', 'some.project.my_pb2')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::cpp_name* output);
      PyObject* Clif_PyObjFrom(const c::cpp_name&, py::PostConv);
      bool Clif_PyObjAs(PyObject*, std::unique_ptr<c::cpp_name>*);
    """))

  def testProtoEnumType(self):
    c = types.ProtoEnumType('c::name::cpp_name', 'fq.py.path')
    header = '\n'.join(c.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name, py::PostConv);
    """))

  def testCallableType(self):
    t = types.CallableType('cname::cpp_type', '(x:py)->None', 'lambda_Name_def')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // (x:py)->None
      PyObject* Clif_PyObjFrom(cname::cpp_type, py::PostConv);
    """))

  def testCapsuleType(self):
    t = types.CapsuleType('c::name::cpp_name', 'pyname')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name *` as pyname
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      PyObject* Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv);
    """))


class NamespaceTest(unittest.TestCase):

  def testClass1Header(self):
    m = pyext.Module('fq.py.path', for_py3=str is not bytes)
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'py.path', w, w+'_Type', ns,
                        can_copy=False, can_destruct=True,
                        down_cast=None, virtual='', ns='c::name')
    m.types = [t]
    header = '\n'.join(m.GenerateHeader('fq/py/my.clif', 'fq/my.h', {})) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      //////////////////////////////////////////////////////////////////////
      // This file was automatically generated by CLIF to run under Python %d
      // Version 0.2
      //////////////////////////////////////////////////////////////////////
      // source: fq/py/my.clif

      #include <memory>
      #include "clif/python/optional.h"
      #include "fq/my.h"
      #include "clif/python/postconv.h"

      namespace c { namespace name {
      using namespace ::clif;

      // CLIF use `c::name::cpp_name` as py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      PyObject* Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;

      } }  // namespace c::name

      // CLIF init_module if (PyObject* m = PyImport_ImportModule("fq.py.path")) Py_DECREF(m);
      // CLIF init_module else goto err;
    """ % (3 if m.py3output else 2)))

  def testClassHeader(self):
    m = pyext.Module('fq.py.path', for_py3=str is not bytes)
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'py.path.t', w, w+'_Type', ns,
                        can_copy=False, can_destruct=True,
                        down_cast=None, virtual='', ns='c')
    u = types.ClassType('other::cpp_name', 'py.path.u', w, w+'_Type', ns,
                        can_copy=False, can_destruct=True,
                        down_cast=None, virtual='', ns='other')
    m.types = [t, u]
    header = '\n'.join(m.GenerateHeader('fq/py/my.clif', 'fq/my.h', {})) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      //////////////////////////////////////////////////////////////////////
      // This file was automatically generated by CLIF to run under Python %d
      // Version 0.2
      //////////////////////////////////////////////////////////////////////
      // source: fq/py/my.clif

      #include <memory>
      #include "clif/python/optional.h"
      #include "fq/my.h"
      #include "clif/python/postconv.h"

      namespace c {
      using namespace ::clif;

      // CLIF use `c::name::cpp_name` as py.path.t
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      PyObject* Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;

      }  // namespace c

      namespace other {
      using namespace ::clif;

      // CLIF use `other::cpp_name` as py.path.u
      bool Clif_PyObjAs(PyObject* input, other::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<other::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<other::cpp_name>* output);
      PyObject* Clif_PyObjFrom(other::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<other::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<other::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(const other::cpp_name*, py::PostConv) = delete;
      PyObject* Clif_PyObjFrom(const other::cpp_name&, py::PostConv) = delete;

      }  // namespace other

      // CLIF init_module if (PyObject* m = PyImport_ImportModule("fq.py.path")) Py_DECREF(m);
      // CLIF init_module else goto err;
    """ % (3 if m.py3output else 2)))


class MangleTest(unittest.TestCase):

  def testMangle(self):
    self.assertEqual(types.Mangle('::A<B*, const C&>'), 'A_B_ptr_constC_ref')
    self.assertEqual(types.Mangle('::A<B::C>'), 'A_B_C')
    self.assertEqual(types.Mangle('Abc'), 'Abc')
    self.assertEqual(types.Mangle('Abc::D'), 'Abc_D')
    self.assertEqual(types.Mangle('Abc<D>'), 'Abc_D')
    self.assertEqual(types.Mangle('Abc<D>&&'), 'Abc_D__rref')
    self.assertEqual(types.Mangle('Abc<D::E>'), 'Abc_D_E')
    self.assertEqual(types.Mangle('Abc<D *> *'), 'Abc_D_ptr__ptr')
    self.assertEqual(types.Mangle('Abc<const D *> *'), 'Abc_constD_ptr__ptr')
    self.assertEqual(types.Mangle('Abc const&'), 'Abcconst_ref')


if __name__ == '__main__':
  unittest.main()
