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
from clif.python import clif_types as types


class TypesTest(absltest.TestCase):

  def testClassType(self):
    ns = 'clif::name::'
    w = ns+'wrapper'
    t = types.ClassType('c::name::cpp_name', 'fq.py.path', w, w+'_Type', ns,
                        can_copy=False, can_move=False, can_destruct=True,
                        virtual='', suppress_shared_ptr_const_conversion=False)
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<const c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<const c::name::cpp_name>, py::PostConv);
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
                        virtual='', suppress_shared_ptr_const_conversion=False)
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<const c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<const c::name::cpp_name>, py::PostConv);
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
                        can_destruct=True, virtual='',
                        suppress_shared_ptr_const_conversion=False)
    header = '\n'.join(t.GenHeader()) + '\n'
    self.assertMultiLineEqual(header, textwrap.dedent("""\
      // CLIF use `c::name::cpp_name` as fq.py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<const c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<const c::name::cpp_name>, py::PostConv);
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


def _GenerateHeaderHelper(t_pp, t_ns, u_ns=None,
                          private='', is_extended_from_python=False):
  m = pyext.Module(f'fq.py.{private}path')
  ns = 'clif::name::'
  w = ns+'wrapper'
  m.types = [
      types.ClassType('c::name::cpp_name', t_pp, w, w+'_Type', ns,
                      can_copy=False, can_move=False, can_destruct=True,
                      virtual='', ns=t_ns,
                      suppress_shared_ptr_const_conversion=False)]
  if u_ns is not None:
    m.types.append(
        types.ClassType('other::cpp_name', 'py.path.u', w, w+'_Type', ns,
                        can_copy=False, can_move=False, can_destruct=True,
                        virtual='', ns=u_ns,
                        suppress_shared_ptr_const_conversion=False))
  return (
      '\n'.join(
          m.GenerateHeader(
              'fq/py/my.clif', 123456789, 'fq/my.h', {}, is_extended_from_python
          )
      )
      + '\n'
  )


class NamespaceTest(absltest.TestCase):

  def testClass1Header(self):
    header = _GenerateHeaderHelper(t_pp='py.path', t_ns='c::name')
    self.assertMultiLineEqual(
        header,
        textwrap.dedent("""\
      // This file was automatically generated by PyCLIF-C-API.
      // clif_matcher_version_stamp: 123456789
      // source: fq/py/my.clif

      #if !defined(PYCLIF_CC_LIBRARY_REQUIREMENT_IS_MET) && !defined(PYBIND11_VERSION_HEX)
      #error http://go/pyclif_cc_library_requirement
      #endif

      #include <memory>
      #include "absl/types/optional.h"
      #include "fq/my.h"
      #include "clif/python/postconv.h"

      namespace c { namespace name {
      using namespace ::clif;

      // CLIF use `c::name::cpp_name` as py.path
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<const c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<const c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<c::name::cpp_name>, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, c::name::cpp_name>::value>::type Clif_PyObjFrom(const c::name::cpp_name&, py::PostConv) = delete;

      } }  // namespace c::name

      // CLIF init_module if (PyObject* m = PyImport_ImportModule("fq.py.path")) Py_DECREF(m);
      // CLIF init_module else goto err;
    """),
    )

  def testClassHeader(self):
    header = _GenerateHeaderHelper(t_pp='py.path.t', t_ns='c', u_ns='other')
    self.assertMultiLineEqual(
        header,
        textwrap.dedent("""\
      // This file was automatically generated by PyCLIF-C-API.
      // clif_matcher_version_stamp: 123456789
      // source: fq/py/my.clif

      #if !defined(PYCLIF_CC_LIBRARY_REQUIREMENT_IS_MET) && !defined(PYBIND11_VERSION_HEX)
      #error http://go/pyclif_cc_library_requirement
      #endif

      #include <memory>
      #include "absl/types/optional.h"
      #include "fq/my.h"
      #include "clif/python/postconv.h"

      namespace c {
      using namespace ::clif;

      // CLIF use `c::name::cpp_name` as py.path.t
      bool Clif_PyObjAs(PyObject* input, c::name::cpp_name** output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<const c::name::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<c::name::cpp_name>* output);
      PyObject* Clif_PyObjFrom(c::name::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<c::name::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<const c::name::cpp_name>, py::PostConv);
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
      bool Clif_PyObjAs(PyObject* input, std::shared_ptr<const other::cpp_name>* output);
      bool Clif_PyObjAs(PyObject* input, std::unique_ptr<other::cpp_name>* output);
      PyObject* Clif_PyObjFrom(other::cpp_name*, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<other::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::shared_ptr<const other::cpp_name>, py::PostConv);
      PyObject* Clif_PyObjFrom(std::unique_ptr<other::cpp_name>, py::PostConv);
      template<typename T>
      typename std::enable_if<std::is_same<T, other::cpp_name>::value>::type Clif_PyObjFrom(const other::cpp_name*, py::PostConv) = delete;
      template<typename T>
      typename std::enable_if<std::is_same<T, other::cpp_name>::value>::type Clif_PyObjFrom(const other::cpp_name&, py::PostConv) = delete;

      }  // namespace other

      // CLIF init_module if (PyObject* m = PyImport_ImportModule("fq.py.path")) Py_DECREF(m);
      // CLIF init_module else goto err;
    """),
    )

  def testOptionImportViaPythonLayer(self):
    t_pp = 'py.path.t'
    t_ns = 'c'
    header = _GenerateHeaderHelper(t_pp, t_ns, private='_')
    self.assertIn('PyImport_ImportModule("fq.py._path")', header)
    header = _GenerateHeaderHelper(t_pp, t_ns, private='_',
                                   is_extended_from_python=True)
    self.assertIn('PyImport_ImportModule("fq.py.path")', header)
    with self.assertRaises(ValueError) as ctx:
      _GenerateHeaderHelper(t_pp, t_ns, is_extended_from_python=True)
    self.assertEqual(
        str(ctx.exception),
        'OPTION is_extended_from_python is applicable only to private'
        ' extensions (i.e. the unqualified name of the extension must start'
        ' with an underscore). Fully-qualified extension name: fq.py.path')


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
