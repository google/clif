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

"""Tests for GenFunc from clif.python.generator."""

import textwrap
from google.protobuf import text_format
import unittest
from clif.protos import ast_pb2
from clif.python import pyext


class FuncTest(unittest.TestCase):

  def setUp(self):
    tm = ast_pb2.Typemap()
    text_format.Parse("""
        lang_type: "str"
        postconversion: "SomeFunc"
      """, tm)
    self.m = pyext.Module('my.test', typemap=[tm])

  def assertFuncEqual(self, proto, code):
    ast = ast_pb2.FuncDecl()
    text_format.Parse(proto, ast)
    out = '\n'.join(self.m.WrapFunc(ast, -1, ''))+'\n'
    self.assertMultiLineEqual(out, textwrap.dedent(code))

  def testVoidFunc0(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
    """, """
      // f()
      static PyObject* wrapf(PyObject* self) {
        // Call actual C++ method.
        f();
        Py_RETURN_NONE;
      }
    """)

  def testIntFunc0Async(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      async: true
      returns {
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
    """, """
      // f() -> int
      static PyObject* wrapf(PyObject* self) {
        // Call actual C++ method.
        PyThreadState* _save;
        Py_UNBLOCK_THREADS
        int32 ret0 = f();
        Py_BLOCK_THREADS
        return Clif_PyObjFrom(std::move(ret0), {});
      }
    """)

  def testIntFunc0Post(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      returns {
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
      postproc: "f.q.Post"
    """, """
      // f() -> int
      static PyObject* wrapf(PyObject* self) {
        // Call actual C++ method.
        int32 ret0 = f();
        // Convert return values to Python.
        PyObject* p, * result_tuple = PyTuple_New(1);
        if (result_tuple == nullptr) return nullptr;
        if ((p=Clif_PyObjFrom(std::move(ret0), {})) == nullptr) {
          Py_DECREF(result_tuple);
          return nullptr;
        }
        PyTuple_SET_ITEM(result_tuple, 0, p);
        PyObject* pyproc = ImportFQName("f.q.Post");
        if (pyproc == nullptr) {
          Py_DECREF(result_tuple);
          return nullptr;
        }
        p = PyObject_CallObject(pyproc, result_tuple);
        Py_DECREF(pyproc);
        Py_CLEAR(result_tuple);
        result_tuple = p;
        return result_tuple;
      }
    """)

  def testIntFunc0Catch(self):
    self.m.catch_cpp_exceptions = True
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      async: true
      returns {
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
    """, """
      // f() -> int
      static PyObject* wrapf(PyObject* self) {
        // Call actual C++ method.
        PyThreadState* _save;
        Py_UNBLOCK_THREADS
        int32 ret0;
        PyObject* err_type = nullptr;
        string err_msg{"C++ exception"};
        try {
          ret0 = f();
        } catch(const std::exception& e) {
          err_type = PyExc_RuntimeError;
          err_msg += string(": ") + e.what();
        } catch (...) {
          err_type = PyExc_RuntimeError;
        }
        Py_BLOCK_THREADS
        if (err_type) {
          PyErr_SetString(err_type, err_msg.c_str());
          return nullptr;
        }
        return Clif_PyObjFrom(std::move(ret0), {});
      }
    """)

  def testVoidFunc1(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      params {
        name {
          native: "a"
        }
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
    """, """
      // f(a:int)
      static PyObject* wrapf(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[1];
        char* names[] = {
            C("a"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "O:f", names, &a[0])) return nullptr;
        int32 arg1;
        if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("f", names[0], "int32", a[0]);
        // Call actual C++ method.
        f(std::move(arg1));
        Py_RETURN_NONE;
      }
    """)

  def testVoidFunc1Async(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      async: true
      params {
        name {
          native: "a"
        }
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
    """, """
      // f(a:int)
      static PyObject* wrapf(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[1];
        char* names[] = {
            C("a"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "O:f", names, &a[0])) return nullptr;
        int32 arg1;
        if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("f", names[0], "int32", a[0]);
        // Call actual C++ method.
        Py_INCREF(args);
        Py_XINCREF(kw);
        PyThreadState* _save;
        Py_UNBLOCK_THREADS
        f(std::move(arg1));
        Py_BLOCK_THREADS
        Py_DECREF(args);
        Py_XDECREF(kw);
        Py_RETURN_NONE;
      }
    """)

  def testVoidFunc1Ptr(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      params {
        name {
          native: "a"
        }
        type {
          lang_type: "Foo"
          cpp_type: "::Foo *"
          cpp_raw_pointer: true
          cpp_toptr_conversion: true
        }
      }
    """, """
      // f(a:Foo)
      static PyObject* wrapf(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[1];
        char* names[] = {
            C("a"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "O:f", names, &a[0])) return nullptr;
        ::Foo * arg1;
        if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("f", names[0], "::Foo *", a[0]);
        // Call actual C++ method.
        f(arg1);
        Py_RETURN_NONE;
      }
    """)

  def testVoidFunc2(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      params {
        name {
          native: "a"
          cpp_name: "a"
        }
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
      params {
        name {
          native: "b"
          cpp_name: "b"
        }
        type {
          lang_type: "bool"
          cpp_type: "bool"
        }
      }
    """, """
      // f(a:int, b:bool)
      static PyObject* wrapf(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[2];
        char* names[] = {
            C("a"),
            C("b"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "OO:f", names, &a[0], &a[1])) return nullptr;
        int32 arg1;
        if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("f", names[0], "int32", a[0]);
        bool arg2;
        if (!Clif_PyObjAs(a[1], &arg2)) return ArgError("f", names[1], "bool", a[1]);
        // Call actual C++ method.
        f(std::move(arg1), std::move(arg2));
        Py_RETURN_NONE;
      }
    """)

  def testVoidFunc2opt(self):
    self.assertFuncEqual("""
      name {
        native: "F"
        cpp_name: "f"
      }
      params {
        name {
          native: "a"
          cpp_name: "a"
        }
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
        default_value: "default"
      }
      params {
        name {
          native: "b"
          cpp_name: "b"
        }
        type {
          lang_type: "bool"
          cpp_type: "bool"
        }
        default_value: "B_default"
      }
    """, """
      // F(a:int=default, b:bool=default)
      static PyObject* wrapf_as_F(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[2]{};
        char* names[] = {
            C("a"),
            C("b"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "|OO:F", names, &a[0], &a[1])) return nullptr;
        int nargs;  // Find how many args actually passed in.
        for (nargs = 2; nargs > 0; --nargs) {
          if (a[nargs-1] != nullptr) break;
        }
        int32 arg1;
        if (nargs > 0) {
          if (!a[0]) return DefaultArgMissedError("F", names[0]);
          if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("F", names[0], "int32", a[0]);
        }
        bool arg2;
        if (nargs > 1) {
          if (!a[1]) arg2 = (bool)B_default;
          else if (!Clif_PyObjAs(a[1], &arg2)) return ArgError("F", names[1], "bool", a[1]);
        }
        // Call actual C++ method.
        switch (nargs) {
        case 0:
          f(); break;
        case 1:
          f(std::move(arg1)); break;
        case 2:
          f(std::move(arg1), std::move(arg2)); break;
        }
        Py_RETURN_NONE;
      }
    """)

  def testIntFunc2opt1(self):
    self.assertFuncEqual("""
      name {
        native: "F"
        cpp_name: "f"
      }
      params {
        name {
          native: "a"
          cpp_name: "a"
        }
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
      params {
        name {
          native: "b"
          cpp_name: "b"
        }
        type {
          lang_type: "bool"
          cpp_type: "bool"
        }
        default_value: "0"
      }
      returns {
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
    """, """
      // F(a:int, b:bool=default) -> int
      static PyObject* wrapf_as_F(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[2]{};
        char* names[] = {
            C("a"),
            C("b"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "O|O:F", names, &a[0], &a[1])) return nullptr;
        int nargs;  // Find how many args actually passed in.
        for (nargs = 2; nargs > 1; --nargs) {
          if (a[nargs-1] != nullptr) break;
        }
        int32 arg1;
        if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("F", names[0], "int32", a[0]);
        bool arg2;
        if (nargs > 1) {
          if (!a[1]) arg2 = (bool)0;
          else if (!Clif_PyObjAs(a[1], &arg2)) return ArgError("F", names[1], "bool", a[1]);
        }
        // Call actual C++ method.
        int32 ret0;
        switch (nargs) {
        case 1:
          ret0 = f(std::move(arg1)); break;
        case 2:
          ret0 = f(std::move(arg1), std::move(arg2)); break;
        }
        return Clif_PyObjFrom(std::move(ret0), {});
      }
    """)

  def testReturnsBoolStrFunc1(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      params {
        name {
          native: "a"
          cpp_name: "a"
        }
        type {
          lang_type: "int"
          cpp_type: "int32"
        }
      }
      returns {
        name {
          native: "x"
          cpp_name: "x"
        }
        type {
          lang_type: "bool"
          cpp_type: "bool"
        }
      }
      returns {
        name {
          native: "y"
          cpp_name: "y"
        }
        type {
          lang_type: "str"
          cpp_type: "string"
        }
      }
    """, """
      // f(a:int) -> (x:bool, y:str)
      static PyObject* wrapf(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[1];
        char* names[] = {
            C("a"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "O:f", names, &a[0])) return nullptr;
        int32 arg1;
        if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("f", names[0], "int32", a[0]);
        string ret1{};
        // Call actual C++ method.
        bool ret0 = f(std::move(arg1), &ret1);
        // Convert return values to Python.
        PyObject* p, * result_tuple = PyTuple_New(2);
        if (result_tuple == nullptr) return nullptr;
        if ((p=Clif_PyObjFrom(std::move(ret0), {})) == nullptr) {
          Py_DECREF(result_tuple);
          return nullptr;
        }
        PyTuple_SET_ITEM(result_tuple, 0, p);
        if ((p=Clif_PyObjFrom(std::move(ret1), SomeFunc)) == nullptr) {
          Py_DECREF(result_tuple);
          return nullptr;
        }
        PyTuple_SET_ITEM(result_tuple, 1, p);
        return result_tuple;
      }
    """)

  def testVoidFunc1cb(self):
    self.assertFuncEqual("""
      name {
        native: "f"
        cpp_name: "f"
      }
      params {
        name {
          native: "cb"
        }
        type {
          lang_type: "(in:list<int>)->None"
          callable {
            params {
              name {
                native: "in"
                cpp_name: "in"
              }
              type {
                lang_type: "list<int>"
                cpp_type: "::std::vector<int, ::std::allocator<int> >"
                params {
                  lang_type: "int"
                  cpp_type: "int"
                }
              }
              cpp_exact_type: "const ::std::vector<int, ::std::allocator<int> > &"
            }
          }
        }
      }
    """, """
      // f(cb:(in:list<int>)->None)
      static PyObject* wrapf(PyObject* self, PyObject* args, PyObject* kw) {
        PyObject* a[1];
        char* names[] = {
            C("cb"),
            nullptr
        };
        if (!PyArg_ParseTupleAndKeywords(args, kw, "O:f", names, &a[0])) return nullptr;
        std::function<void(const ::std::vector<int, ::std::allocator<int> > &)> arg1;
        if (!Clif_PyObjAs(a[0], &arg1)) return ArgError("f", names[0], "", a[0]);
        // Call actual C++ method.
        f(std::move(arg1));
        Py_RETURN_NONE;
      }
    """)


if __name__ == '__main__':
  unittest.main()
