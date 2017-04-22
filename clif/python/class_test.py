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

"""Tests for clif.python.generator."""

import itertools
import textwrap
from google.protobuf import text_format
import unittest
from clif.protos import ast_pb2
from clif.python import pyext

PATH = 'path.to.ext.module.test'


class ClassTest(unittest.TestCase):

  def setUp(self):
    self.m = pyext.Module(PATH)
    self.code = (dict(tochar='PyUnicode_AsUTF8', f='',
                      frchar='PyUnicode_FromString') if self.m.py3output
                 else
                 dict(tochar='PyString_AS_STRING',
                      frchar='PyString_FromString',
                      f=' | Py_TPFLAGS_CHECKTYPES'))

  def assertClassEqual(self, proto, class_code, mod_code):
    ast = ast_pb2.ClassDecl()
    text_format.Parse(proto, ast)
    out = '\n'.join(self.m.WrapClass(ast, -1, ''))+'\n'
    self.assertMultiLineEqual(out, textwrap.dedent(class_code))
    out = '\n'.join(itertools.chain(
        self.m.GenTypesReady(),
        self.m.GenInitFunction('test.h'),
        ))+'\n'
    self.assertMultiLineEqual(out, textwrap.dedent(mod_code))

  def assertEnumEqual(self, proto, base_code, mod_code):
    ast = ast_pb2.EnumDecl()
    text_format.Parse(proto, ast)
    out = '\n'.join(self.m.WrapEnum(ast, -1, ''))+'\n'
    self.assertMultiLineEqual(out, textwrap.dedent(base_code))
    out = '\n'.join(itertools.chain(
        self.m.GenTypesReady(),
        self.m.GenInitFunction('test.h'),
        ))+'\n'
    self.assertMultiLineEqual(out, textwrap.dedent(mod_code))

  def testStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructTy"
      }
      members {
        decltype: VAR
        var {
          name {
            native: "a"
            cpp_name: "a"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
        }
      }
    """, """
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<StructTy> cpp;
      };
      static StructTy* ThisPtr(PyObject*);

      static PyObject* get_a(PyObject* self, void* xdata) {
        auto cpp = ThisPtr(self); if (!cpp) return nullptr;
        return Clif_PyObjFrom(cpp->a, {});
      }

      static int set_a(PyObject* self, PyObject* value, void* xdata) {
        if (value == nullptr) {
          PyErr_SetString(PyExc_TypeError, "Cannot delete the a attribute");
          return -1;
        }
        auto cpp = ThisPtr(self); if (!cpp) return -1;
        if (Clif_PyObjAs(value, &cpp->a)) return 0;
        PyObject* s = PyObject_Repr(value);
        PyErr_Format(PyExc_ValueError, "%%s is not valid for a:int", s? %(tochar)s(s): "input");
        Py_XDECREF(s);
        return -1;
      }

      static PyGetSetDef Properties[] = {
        {C("a"), get_a, set_a, C("C++ int StructTy.a")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for StructTy",         // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        nullptr,                             // tp_methods
        nullptr,                             // tp_members
        Properties,                          // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("StructTy"));
            if (!PyErr_Occurred()) {
              StructTy* c = static_cast<StructTy*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testCppDerivedStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructTy"
      }
      bases {
        cpp_name: "::Base<Foo*, const Bar&>"
      }
      members {
        decltype: VAR
        var {
          name {
            native: "a"
            cpp_name: "a"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
        }
      }
    """, """
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<StructTy> cpp;
      };
      static StructTy* ThisPtr(PyObject*);

      static PyObject* get_a(PyObject* self, void* xdata) {
        auto cpp = ThisPtr(self); if (!cpp) return nullptr;
        return Clif_PyObjFrom(cpp->a, {});
      }

      static int set_a(PyObject* self, PyObject* value, void* xdata) {
        if (value == nullptr) {
          PyErr_SetString(PyExc_TypeError, "Cannot delete the a attribute");
          return -1;
        }
        auto cpp = ThisPtr(self); if (!cpp) return -1;
        if (Clif_PyObjAs(value, &cpp->a)) return 0;
        PyObject* s = PyObject_Repr(value);
        PyErr_Format(PyExc_ValueError, "%%s is not valid for a:int", s? %(tochar)s(s): "input");
        Py_XDECREF(s);
        return -1;
      }

      static PyGetSetDef Properties[] = {
        {C("a"), get_a, set_a, C("C++ int StructTy.a")},
        {}
      };

      // Implicit cast this as ::Base<Foo*, const Bar&>*
      static PyObject* as_Base_Foo_ptr_constBar_ref(PyObject* self) {
        ::Base<Foo*, const Bar&>* p = ::clif::python::Get(reinterpret_cast<wrapper*>(self)->cpp);
        if (p == nullptr) return nullptr;
        return PyCapsule_New(p, C("::Base<Foo*, const Bar&>"), nullptr);
      }

      static PyMethodDef Methods[] = {
        {C("as_Base_Foo_ptr_constBar_ref"), (PyCFunction)as_Base_Foo_ptr_constBar_ref, METH_NOARGS, C("Upcast to ::Base<Foo*, const Bar&>*")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for StructTy",         // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        Methods,                             // tp_methods
        nullptr,                             // tp_members
        Properties,                          // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("StructTy"));
            if (!PyErr_Occurred()) {
              StructTy* c = static_cast<StructTy*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testPythonDerivedStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructTy"
      }
      bases {
        native: "path.python.Base"
      }
      members {
        decltype: VAR
        var {
          name {
            native: "a"
            cpp_name: "a"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
        }
      }
    """, """
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<StructTy> cpp;
      };
      static StructTy* ThisPtr(PyObject*);

      static PyObject* get_a(PyObject* self, void* xdata) {
        auto cpp = ThisPtr(self); if (!cpp) return nullptr;
        return Clif_PyObjFrom(cpp->a, {});
      }

      static int set_a(PyObject* self, PyObject* value, void* xdata) {
        if (value == nullptr) {
          PyErr_SetString(PyExc_TypeError, "Cannot delete the a attribute");
          return -1;
        }
        auto cpp = ThisPtr(self); if (!cpp) return -1;
        if (Clif_PyObjAs(value, &cpp->a)) return 0;
        PyObject* s = PyObject_Repr(value);
        PyErr_Format(PyExc_ValueError, "%%s is not valid for a:int", s? %(tochar)s(s): "input");
        Py_XDECREF(s);
        return -1;
      }

      static PyGetSetDef Properties[] = {
        {C("a"), get_a, set_a, C("C++ int StructTy.a")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for StructTy",         // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        nullptr,                             // tp_methods
        nullptr,                             // tp_members
        Properties,                          // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("StructTy"));
            if (!PyErr_Occurred()) {
              StructTy* c = static_cast<StructTy*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        PyObject* base_cls = ImportFQName("path.python.Base");
        if (base_cls == nullptr) return false;
        if (!PyObject_TypeCheck(base_cls, &PyType_Type)) {
          Py_DECREF(base_cls);
          PyErr_SetString(PyExc_TypeError, "Base class path.python.Base is not a new style class inheriting from object.");
          return false;
        }
        pyStruct::wrapper_Type.tp_base = reinterpret_cast<PyTypeObject*>(base_cls);
        // Check that base_cls is a *statically* allocated PyType.
        if (pyStruct::wrapper_Type.tp_base->tp_alloc == PyType_GenericAlloc) {
          Py_DECREF(base_cls);
          PyErr_SetString(PyExc_TypeError, "Base class path.python.Base is a dynamic (Python defined) class.");
          return false;
        }
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testNestedStruct(self):
    self.assertClassEqual("""
      name {
        native: "Outer"
        cpp_name: "OutKlass"
      }
      members {
        decltype: CLASS
        class_ {
          name {
            native: "Inner"
            cpp_name: "OutKlass::InnKlass"
          }
          members {
            decltype: VAR
            var {
              name {
                native: "i"
                cpp_name: "i"
              }
              type {
                lang_type: "bool"
                cpp_type: "bool"
              }
            }
          }
          members {
            decltype: ENUM
            enum {
              name {
                native: "X"
                cpp_name: "OutKlass::InnKlass::X"
              }
              members {
                native: "A"
                cpp_name: "OutKlass::InnKlass::X::A"
              }
            }
          }
        }
      }
    """, """
      namespace pyOuter {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<OutKlass> cpp;
      };
      static OutKlass* ThisPtr(PyObject*);

      namespace pyInner {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<OutKlass::InnKlass> cpp;
      };
      static OutKlass::InnKlass* ThisPtr(PyObject*);

      static PyObject* get_i(PyObject* self, void* xdata) {
        auto cpp = ThisPtr(self); if (!cpp) return nullptr;
        return Clif_PyObjFrom(cpp->i, {});
      }

      static int set_i(PyObject* self, PyObject* value, void* xdata) {
        if (value == nullptr) {
          PyErr_SetString(PyExc_TypeError, "Cannot delete the i attribute");
          return -1;
        }
        auto cpp = ThisPtr(self); if (!cpp) return -1;
        if (Clif_PyObjAs(value, &cpp->i)) return 0;
        PyObject* s = PyObject_Repr(value);
        PyErr_Format(PyExc_ValueError, "%%s is not valid for i:bool", s? %(tochar)s(s): "input");
        Py_XDECREF(s);
        return -1;
      }

      // Create Python Enum object (cached in _X) for OutKlass::InnKlass::X
      static PyObject* wrapX() {
        PyObject *py, *py_enum_class{}, *names = PyTuple_New(1);
        if (names == nullptr) return nullptr;
        if ((py = Py_BuildValue("(NN)", %(frchar)s("A"), PyInt_FromLong(
              static_cast<typename std::underlying_type<OutKlass::InnKlass::X>::type>(OutKlass::InnKlass::X::A)))
            ) == nullptr) goto err;
        PyTuple_SET_ITEM(names, 0, py);
        py = %(frchar)s("Outer.Inner.X");
        py_enum_class = PyObject_CallFunctionObjArgs(path_to_ext_module_test_clifwrap::_IntEnum, py, names, nullptr);
        Py_DECREF(py);
      err:
        Py_DECREF(names);
        return py_enum_class;
      }
      static PyObject* _X{};  // set by above func in Init()

      static PyGetSetDef Properties[] = {
        {C("i"), get_i, set_i, C("C++ bool OutKlass::InnKlass.i")},
        {}
      };

      // Inner __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Inner __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Outer.Inner", // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for OutKlass::InnKlass", // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        nullptr,                             // tp_methods
        nullptr,                             // tp_members
        Properties,                          // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Inner takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<OutKlass::InnKlass>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static OutKlass::InnKlass* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_OutKlass_InnKlass"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("OutKlass::InnKlass"));
            if (!PyErr_Occurred()) {
              OutKlass::InnKlass* c = static_cast<OutKlass::InnKlass*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to OutKlass::InnKlass*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyInner

      // Outer __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Outer __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Outer",     // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for OutKlass",         // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        nullptr,                             // tp_methods
        nullptr,                             // tp_members
        nullptr,                             // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Outer takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<OutKlass>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static OutKlass* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_OutKlass"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("OutKlass"));
            if (!PyErr_Occurred()) {
              OutKlass* c = static_cast<OutKlass*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to OutKlass*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyOuter
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyOuter::pyInner::wrapper_Type) < 0) return false;
        Py_INCREF(&pyOuter::pyInner::wrapper_Type);  // For PyModule_AddObject to steal.
        if (PyType_Ready(&pyOuter::wrapper_Type) < 0) return false;
        Py_INCREF(&pyOuter::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        {PyObject* em = PyImport_ImportModule("enum");
         if (em == nullptr) goto err;
         _Enum = PyObject_GetAttrString(em, "Enum");
         _IntEnum = PyObject_GetAttrString(em, "IntEnum");
         Py_DECREF(em);}
        if (!_Enum || !_IntEnum) {
          Py_XDECREF(_Enum);
          Py_XDECREF(_IntEnum);
          goto err;
        }
        if (PyDict_SetItemString(pyOuter::pyInner::wrapper_Type.tp_dict, "X", (pyOuter::pyInner::_X=pyOuter::pyInner::wrapX())) < 0) goto err;
        if (PyDict_SetItemString(pyOuter::wrapper_Type.tp_dict, "Inner", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyOuter::pyInner::wrapper_Type)) < 0) goto err;
        if (PyModule_AddObject(module, "Outer", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyOuter::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        {PyObject* em = PyImport_ImportModule("enum");
         if (em == nullptr) goto err;
         _Enum = PyObject_GetAttrString(em, "Enum");
         _IntEnum = PyObject_GetAttrString(em, "IntEnum");
         Py_DECREF(em);}
        if (!_Enum || !_IntEnum) {
          Py_XDECREF(_Enum);
          Py_XDECREF(_IntEnum);
          goto err;
        }
        if (PyDict_SetItemString(pyOuter::pyInner::wrapper_Type.tp_dict, "X", (pyOuter::pyInner::_X=pyOuter::pyInner::wrapX())) < 0) goto err;
        if (PyDict_SetItemString(pyOuter::wrapper_Type.tp_dict, "Inner", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyOuter::pyInner::wrapper_Type)) < 0) goto err;
        if (PyModule_AddObject(module, "Outer", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyOuter::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testStructProperty(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructTy"
      }
      members {
        decltype: VAR
        var {
          name {
            native: "a"
            cpp_name: "a"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
          cpp_get {
            name {
              cpp_name: "getA"
            }
            # type omitted
          }
          cpp_set {
            name {
              cpp_name: "setA"
            }
            params {
              type {
                lang_type: "int"
                cpp_type: "int"
              }
            }
            cpp_void_return: true
            cpp_noexcept: false
          }
        }
      }
    """, """
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<StructTy> cpp;
      };
      static StructTy* ThisPtr(PyObject*);

      static PyObject* get_a(PyObject* self, void* xdata) {
        auto cpp = ThisPtr(self); if (!cpp) return nullptr;
        return Clif_PyObjFrom(cpp->getA(), {});
      }

      static int set_a(PyObject* self, PyObject* value, void* xdata) {
        if (value == nullptr) {
          PyErr_SetString(PyExc_TypeError, "Cannot delete the a attribute");
          return -1;
        }
        int cval;
        if (Clif_PyObjAs(value, &cval)) {
          auto cpp = ThisPtr(self); if (!cpp) return -1;
          cpp->setA(cval);
          return 0;
        }
        PyObject* s = PyObject_Repr(value);
        PyErr_Format(PyExc_ValueError, "%%s is not valid for a:int", s? %(tochar)s(s): "input");
        Py_XDECREF(s);
        return -1;
      }

      static PyGetSetDef Properties[] = {
        {C("a"), get_a, set_a, C("C++ int StructTy.getA()")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for StructTy",         // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        nullptr,                             // tp_methods
        nullptr,                             // tp_members
        Properties,                          // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("StructTy"));
            if (!PyErr_Occurred()) {
              StructTy* c = static_cast<StructTy*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testStructUnProperty(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructTy"
      }
      members {
        decltype: VAR
        var {
          name {
            native: "x"
            cpp_name: "a"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
          cpp_get {
            name {
              native: "get_a"
            }
          }
          cpp_set {
            name {
              native: "set_a"
            }
          }
        }
      }
    """, """
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<StructTy> cpp;
      };
      static StructTy* ThisPtr(PyObject*);

      static PyObject* get_a(PyObject* self) {
        auto cpp = ThisPtr(self); if (!cpp) return nullptr;
        return Clif_PyObjFrom(cpp->a, {});
      }

      static PyObject* set_a(PyObject* self, PyObject* value) {
        auto cpp = ThisPtr(self); if (!cpp) return nullptr;
        if (Clif_PyObjAs(value, &cpp->a)) Py_RETURN_NONE;
        PyObject* s = PyObject_Repr(value);
        PyErr_Format(PyExc_ValueError, "%%s is not valid for x:int", s? PyString_AS_STRING(s): "input");
        Py_XDECREF(s);
        return nullptr;
      }

      static PyMethodDef Methods[] = {
        {C("get_a"), (PyCFunction)get_a, METH_NOARGS, C("get_a()->int  C++ StructTy.a getter")},
        {C("set_a"), set_a, METH_O, C("set_a(int)  C++ StructTy.a setter")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for StructTy",         // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        Methods,                             // tp_methods
        nullptr,                             // tp_members
        nullptr,                             // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("StructTy"));
            if (!PyErr_Occurred()) {
              StructTy* c = static_cast<StructTy*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testFinalStructProperty(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructTy"
      }
      members {
        decltype: VAR
        var {
          name {
            native: "a"
            cpp_name: "a"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
          cpp_get {
            name {
              cpp_name: "getA"
            }
            # type omitted
          }
          cpp_set {
            name {
              cpp_name: "setA"
            }
            params {
              type {
                lang_type: "int"
                cpp_type: "int"
              }
            }
            cpp_void_return: true
            cpp_noexcept: false
          }
        }
      }
      members {
        decltype: VAR
        var {
          name {
            native: "b"
            cpp_name: "b"
          }
          type {
            lang_type: "int"
            cpp_type: "int"
          }
          cpp_get {
            name {
              cpp_name: "getB"
            }
            # type omitted
          }
        }
      }
      final: true
    """, """
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<StructTy> cpp;
      };

      static PyObject* get_a(PyObject* self, void* xdata) {
        return Clif_PyObjFrom(reinterpret_cast<wrapper*>(self)->cpp->getA(), {});
      }

      static int set_a(PyObject* self, PyObject* value, void* xdata) {
        if (value == nullptr) {
          PyErr_SetString(PyExc_TypeError, "Cannot delete the a attribute");
          return -1;
        }
        int cval;
        if (Clif_PyObjAs(value, &cval)) {
          reinterpret_cast<wrapper*>(self)->cpp->setA(cval);
          return 0;
        }
        PyObject* s = PyObject_Repr(value);
        PyErr_Format(PyExc_ValueError, "%%s is not valid for a:int", s? %(tochar)s(s): "input");
        Py_XDECREF(s);
        return -1;
      }

      static PyObject* get_b(PyObject* self, void* xdata) {
        return Clif_PyObjFrom(reinterpret_cast<wrapper*>(self)->cpp->getB(), {});
      }

      static PyGetSetDef Properties[] = {
        {C("a"), get_a, set_a, C("C++ int StructTy.getA()")},
        {C("b"), get_b, nullptr, C("C++ int StructTy.getB()")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s, // tp_flags
        "CLIF wrapper for StructTy",         // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        nullptr,                             // tp_methods
        nullptr,                             // tp_members
        Properties,                          // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testSharedFinalStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructCpp"
      }
      shared: true
      final: true
      members {
        decltype: FUNC
        func {
          name {
            native: "f"
            cpp_name: "f"
          }
        }
      }
    """, r"""
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<StructCpp> cpp;
      };

      // f()
      static PyObject* wrapf(PyObject* self) {
        // Call actual C++ method.
        reinterpret_cast<wrapper*>(self)->cpp->f();
        Py_RETURN_NONE;
      }

      static PyMethodDef Methods[] = {
        {C("f"), (PyCFunction)wrapf, METH_NOARGS, C("f()\n  Calls C++ function\n  void f()")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s, // tp_flags
        "CLIF wrapper for StructCpp",        // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        Methods,                             // tp_methods
        nullptr,                             // tp_members
        nullptr,                             // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructCpp>();
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructCpp* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testVirtualStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructCpp"
      }
      members {
        decltype: FUNC
        func {
          name {
            native: "F"
            cpp_name: "::StructCpp::f"
          }
          virtual: true
        }
      }
    """, r"""
      namespace pyStruct {

      struct Overrider : PyObj, StructCpp {
        using StructCpp::StructCpp;

        void f() override {
          auto f = ::clif::SafeGetAttrString(pythis.get(), C("F"));
          if (f.get()) {
            ::clif::callback::Func<void>(f.get())();
          } else {
            ::StructCpp::f();
          }
        }
      };

      struct wrapper {
        PyObject_HEAD
        ::clif::SharedPtr<Overrider> cpp;
      };
      static StructCpp* ThisPtr(PyObject*);

      // F()
      static PyObject* wrapf_as_F(PyObject* self) {
        // Call actual C++ method.
        StructCpp* c = ThisPtr(self);
        if (!c) return nullptr;
        c->StructCpp::f();
        Py_RETURN_NONE;
      }

      // Implicit cast this as StructCpp*
      static PyObject* as_StructCpp(PyObject* self) {
        StructCpp* p = ::clif::python::Get(reinterpret_cast<wrapper*>(self)->cpp);
        if (p == nullptr) return nullptr;
        return PyCapsule_New(p, C("StructCpp"), nullptr);
      }

      static PyMethodDef Methods[] = {
        {C("F"), (PyCFunction)wrapf_as_F, METH_NOARGS, C("F()\n  Calls C++ function\n  void ::StructCpp::f()")},
        {C("as_StructCpp"), (PyCFunction)as_StructCpp, METH_NOARGS, C("Upcast to StructCpp*")},
        {}
      };

      // Struct __new__
      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems);
      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      static void _dtor(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject wrapper_Type = {
        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        "path.to.ext.module.test.Struct",    // tp_name
        sizeof(wrapper),                     // tp_basicsize
        0,                                   // tp_itemsize
        Clif_PyType_GenericFree,             // tp_dealloc
        nullptr,                             // tp_print
        nullptr,                             // tp_getattr
        nullptr,                             // tp_setattr
        nullptr,                             // tp_compare
        nullptr,                             // tp_repr
        nullptr,                             // tp_as_number
        nullptr,                             // tp_as_sequence
        nullptr,                             // tp_as_mapping
        nullptr,                             // tp_hash
        nullptr,                             // tp_call
        nullptr,                             // tp_str
        nullptr,                             // tp_getattro
        nullptr,                             // tp_setattro
        nullptr,                             // tp_as_buffer
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_TYPE_SUBCLASS%(f)s | Py_TPFLAGS_BASETYPE, // tp_flags
        "CLIF wrapper for StructCpp",        // tp_doc
        nullptr,                             // tp_traverse
        nullptr,                             // tp_clear
        nullptr,                             // tp_richcompare
        0,                                   // tp_weaklistoffset
        nullptr,                             // tp_iter
        nullptr,                             // tp_iternext
        Methods,                             // tp_methods
        nullptr,                             // tp_members
        nullptr,                             // tp_getset
        nullptr,                             // tp_base
        nullptr,                             // tp_dict
        nullptr,                             // tp_descr_get
        nullptr,                             // tp_descr_set
        0,                                   // tp_dictoffset
        _ctor,                               // tp_init
        _allocator,                          // tp_alloc
        PyType_GenericNew,                   // tp_new
        _dtor,                               // tp_free
        nullptr,                             // tp_is_gc
        nullptr,                             // tp_bases
        nullptr,                             // tp_mro
        nullptr,                             // tp_cache
        nullptr,                             // tp_subclasses
        nullptr,                             // tp_weaklist
        nullptr,                             // tp_del
        0,                                   // tp_version_tag
      };

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<Overrider>();
        reinterpret_cast<wrapper*>(self)->cpp->::clif::PyObj::Init(self);
        return 0;
      }

      static PyObject* _allocator(PyTypeObject* type, Py_ssize_t nitems) {
        assert(nitems == 0);
        PyObject* self = reinterpret_cast<PyObject*>(new wrapper);
        return PyObject_Init(self, &wrapper_Type);
      }

      static StructCpp* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == &wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructCpp"), nullptr);
        if (base) {
          if (PyCapsule_CheckExact(base)) {
            void* p = PyCapsule_GetPointer(base, C("StructCpp"));
            if (!PyErr_Occurred()) {
              StructCpp* c = static_cast<StructCpp*>(p);
              Py_DECREF(base);
              return c;
            }
          }
          Py_DECREF(base);
        }
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(&wrapper_Type))) {
          if (!base) {
            PyErr_Clear();
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructCpp*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type.tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }
      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        if (PyType_Ready(&pyStruct::wrapper_Type) < 0) return false;
        Py_INCREF(&pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(&path_to_ext_module_test_clifwrap::pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testEnum(self):
    self.assertEnumEqual("""
      name {
        native: "MyEnum"
        cpp_name: "myEnum"
      }
      members {
        native: "ONE"
        cpp_name: "kOne"
        }
      members {
        cpp_name: "myEnum::TWO"
      }
    """, """
      // Create Python Enum object (cached in _MyEnum) for myEnum
      static PyObject* wrapmyEnum() {
        PyObject *py, *py_enum_class{}, *names = PyTuple_New(2);
        if (names == nullptr) return nullptr;
        if ((py = Py_BuildValue("(NN)", %(frchar)s("ONE"), PyInt_FromLong(
              static_cast<typename std::underlying_type<myEnum>::type>(myEnum::kOne)))
            ) == nullptr) goto err;
        PyTuple_SET_ITEM(names, 0, py);
        if ((py = Py_BuildValue("(NN)", %(frchar)s("TWO"), PyInt_FromLong(
              static_cast<typename std::underlying_type<myEnum>::type>(myEnum::TWO)))
            ) == nullptr) goto err;
        PyTuple_SET_ITEM(names, 1, py);
        py = %(frchar)s("MyEnum");
        py_enum_class = PyObject_CallFunctionObjArgs(path_to_ext_module_test_clifwrap::_IntEnum, py, names, nullptr);
        Py_DECREF(py);
      err:
        Py_DECREF(names);
        return py_enum_class;
      }
      static PyObject* _MyEnum{};  // set by above func in Init()
    """ % self.code, """
      bool Ready() {
        return true;
      }

      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        "path.to.ext.module.test",  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        {PyObject* em = PyImport_ImportModule("enum");
         if (em == nullptr) goto err;
         _Enum = PyObject_GetAttrString(em, "Enum");
         _IntEnum = PyObject_GetAttrString(em, "IntEnum");
         Py_DECREF(em);}
        if (!_Enum || !_IntEnum) {
          Py_XDECREF(_Enum);
          Py_XDECREF(_IntEnum);
          goto err;
        }
        if (PyModule_AddObject(module, "MyEnum", (_MyEnum=wrapmyEnum())) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      bool Ready() {
        return true;
      }

      PyObject* Init() {
        PyObject* module = Py_InitModule3("path.to.ext.module.test", nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        {PyObject* em = PyImport_ImportModule("enum");
         if (em == nullptr) goto err;
         _Enum = PyObject_GetAttrString(em, "Enum");
         _IntEnum = PyObject_GetAttrString(em, "IntEnum");
         Py_DECREF(em);}
        if (!_Enum || !_IntEnum) {
          Py_XDECREF(_Enum);
          Py_XDECREF(_IntEnum);
          goto err;
        }
        if (PyModule_AddObject(module, "MyEnum", (_MyEnum=wrapmyEnum())) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """)


if __name__ == '__main__':
  unittest.main()
