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

"""Tests for types."""

import textwrap
from absl.testing import absltest
from clif.python import pyext
from clif.python import types


class TypesTest(absltest.TestCase):

  def testClassType(self):
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'fq.py.path', w, w+'_Type', ns,
                        can_copy=False, can_move=False, can_destruct=True,
                        virtual='')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;
    """))

  def testClassTypeWithNoDtor(self):
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'fq.py.path', w, w+'_Type', ns,
                        can_copy=False, can_move=False, can_destruct=False,
                        virtual='')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;
    """))

  def testUncopyableButMovableClassType(self):
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'fq.py.path', w, w+'_Type', ns,
                        can_copy=False, can_move=True,
                        can_destruct=True, virtual='')
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(c::name::cpp_name&&, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;
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
      PyObject* Clif_PyObjFrom(std::unique_ptr<const c::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<const c::cpp_name>, py::PostConv);
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
      // CLIF use `c::name::cpp_name*` as pyname
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      PyObject* Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv);
    """))


class NamespaceTest(absltest.TestCase):

  def testClass1Header(self):
    m = pyext.Module('fq.py.path', for_py3=str is not bytes)
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'py.path', w, w+'_Type', ns,
                        can_copy=False, can_move=False, can_destruct=True,
                        virtual='', ns='c::name')
    m.types = [t]
    header = '\n'.join(m.GenerateHeader('fq/py/my.clif', 'fq/my.h', {})) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      //////////////////////////////////////////////////////////////////////
      // This file was automatically generated by CLIF to run under Python %d
      // Version 0.3
      //////////////////////////////////////////////////////////////////////
      // source: fq/py/my.clif

      #include <memory>
      #include "absl/types/optional.h"
      #include "fq/my.h"
      #include "clif/python/postconv.h"

      namespace c { namespace name {
      using namespace ::clif;

      // CLIF use `c::name::cpp_name` as py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;

      } }  // namespace c::name

      // CLIF init_module if (PyObject* m = PyImport_ImportModule("fq.py.path")) Py_DECREF(m);
      // CLIF init_module else goto err;
    """ % (3 if m.py3output else 2)))

  def testClassHeader(self):
    m = pyext.Module('fq.py.path', for_py3=str is not bytes)
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'py.path.t', w, w+'_Type', ns,
                        can_copy=False, can_move=False, can_destruct=True,
                        virtual='', ns='c')
    u = types.ClassType('other::cpp_name', 'py.path.u', w, w+'_Type', ns,
                        can_copy=False, can_move=False, can_destruct=True,
                        virtual='', ns='other')
    m.types = [t, u]
    header = '\n'.join(m.GenerateHeader('fq/py/my.clif', 'fq/my.h', {})) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      //////////////////////////////////////////////////////////////////////
      // This file was automatically generated by CLIF to run under Python %d
      // Version 0.3
      //////////////////////////////////////////////////////////////////////
      // source: fq/py/my.clif

      #include <memory>
      #include "absl/types/optional.h"
      #include "fq/my.h"
      #include "clif/python/postconv.h"

      namespace c {
      using namespace ::clif;

      // CLIF use `c::name::cpp_name` as py.path.t
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;

      }  // namespace c

      namespace other {
      using namespace ::clif;

      // CLIF use `other::cpp_name` as py.path.u
      bool Clif_PyObjAs(PyObject* input, other::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<other::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<other::cpp_name>* output);
      PyObject* Clif_PyObjFrom(other::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<other::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<other::cpp_name>, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, other::cpp_name>::value>::type Clif_PyObjFrom(const other::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, other::cpp_name>::value>::type Clif_PyObjFrom(const other::cpp_name&, py::PostConv) = delete;

      }  // namespace other

      // CLIF init_module if (PyObject* m = PyImport_ImportModule("fq.py.path")) Py_DECREF(m);
      // CLIF init_module else goto err;
    """ % (3 if m.py3output else 2)))


class MangleTest(absltest.TestCase):

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
    self.assertEqual(types.Mangle('A<B, -1>'), 'A_B__1')
    self.assertEqual(types.Mangle("A<B, 'a'>"), 'A_B_c97_')

  def testMangleEscapedCharLiteral(self):
    # Octal escapes.
    self.assertEqual(
        types.Mangle(r"A<'\0', '\000', '\5', '\777'>"), 'A_c0__c0__c5__c511_')

    # Hexadecimal escapes.
    self.assertEqual(
        types.Mangle(r"A<'\x00', '\xff', '\xFF', '\xA0'>"),
        'A_c0__c255__c255__c160_')

    # Unicode escapes.
    self.assertEqual(
        types.Mangle(r"A<'\u0000', '\u0001', '\u1000', '\u9999'>"),
        'A_c0__c1__c4096__c39321_')
    self.assertEqual(
        types.Mangle(r"A<'\U00000000', '\U00109999'>"), 'A_c0__c1087897_')

    # ASCII control code escapes.
    self.assertEqual(
        types.Mangle(r"A<'\a', '\b', '\f', '\n', '\r', '\t', '\v'>"),
        'A_c7__c8__c12__c10__c13__c9__c11_')

    # Other low-ASCII escapes.
    self.assertEqual(
        types.Mangle("A<'\\'', '\\\"', '\\\\'>"), 'A_c39__c34__c92_')


if __name__ == '__main__':
  absltest.main()
