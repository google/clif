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

"""Tests for module init."""

import itertools
import textwrap
import unittest

from google.protobuf import text_format
from clif.protos import ast_pb2
from clif.python import pyext


class ModuleTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.maxDiff = 100000
    self.m = pyext.Module('my.test')

  def testFuncInit(self):
    ast = ast_pb2.AST()
    text_format.Parse("""
      decls {
        decltype: FUNC
        func {
          name {
            native: "x"
            cpp_name: "x_"
          }
          returns {
            type {
              lang_type: "int"
              cpp_type: "int"
            }
          }
        }
      }
    """, ast)
    # Fill context.
    for d in ast.decls:
      list(self.m.WrapDecl(d))
    out = '\n'.join(
        self.m.GenInitFunction('my.h'),
        )
    self.assertMultiLineEqual(out, textwrap.dedent(r"""
    static struct PyModuleDef Module = {
      PyModuleDef_HEAD_INIT,
      ThisModuleName,
      "CLIF-generated module for my.h", // module doc
      -1,  // module keeps state in global variables
      MethodsStaticAlloc,
      nullptr,  // m_slots a.k.a. m_reload
      nullptr,  // m_traverse
      ClearImportCache  // m_clear
    };

    PyObject* Init() {
      PyObject* module = PyModule_Create(&Module);
      if (!module) return nullptr;
      return module;
    }"""))

  def testModConst(self):
    ast = ast_pb2.AST()
    text_format.Parse("""
      decls {
        decltype: CONST
        const {
          name {
            native: "ONE"
            cpp_name: "kOne"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
        }
      }
      extra_init: "if (something_wrong) goto err;"
    """, ast)
    self.m.init += ast.extra_init
    out = '\n'.join(itertools.chain(
        self.m.WrapConst(ast.decls[0].const, -1, ''),
        self.m.GenInitFunction('my.h'),
        ))
    # pylint: disable=g-long-ternary
    self.assertMultiLineEqual(out, textwrap.dedent("""
        static struct PyModuleDef Module = {
          PyModuleDef_HEAD_INIT,
          ThisModuleName,
          "CLIF-generated module for my.h", // module doc
          -1,  // module keeps state in global variables
          nullptr,
          nullptr,  // m_slots a.k.a. m_reload
          nullptr,  // m_traverse
          ClearImportCache  // m_clear
        };

        PyObject* Init() {
          PyObject* module = PyModule_Create(&Module);
          if (!module) return nullptr;
          if (something_wrong) goto err;
          if (PyModule_AddObject(module, "ONE", Clif_PyObjFrom(static_cast<int>(kOne), {})) < 0) goto err;
          return module;
        err:
          Py_DECREF(module);
          return nullptr;
        }"""))
    # pylint: enable=g-long-ternary

  def testModule(self):
    out = '\n'.join(self.m.GenerateInit('my.clif', 123456789))
    # pylint: disable=g-long-ternary
    optional_pyclif_cc_requirement = ""
    expected = textwrap.dedent("""\
      // This file was automatically generated by PyCLIF-C-API.
      // clif_matcher_version_stamp: 123456789
      // source: my.clif

    """) + optional_pyclif_cc_requirement + textwrap.dedent("""\
      #include <Python.h>

      namespace my_test_clifwrap {

      bool Ready();
      PyObject* Init();

      }  // namespace my_test_clifwrap

      PyMODINIT_FUNC PyInit_test(void) {
        if (!my_test_clifwrap::Ready()) return nullptr;
        return my_test_clifwrap::Init();
      }""")

    self.assertMultiLineEqual(out, expected)
    # pylint: enable=g-long-ternary


if __name__ == '__main__':
  unittest.main()
