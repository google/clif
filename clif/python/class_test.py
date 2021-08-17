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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools
import textwrap
import unittest
from google.protobuf import text_format
from clif.protos import ast_pb2
from clif.python import pyext

# If PATH is a full import path, the module can be imported only from that path.
# If the PATH is empty tp_name will contain only module name (eg. Struct)
# allowing to load it from any directory.
PATH = 'path.to.ext.module.test'

# This test is not worth a large-scale cleanup:
# pylint: disable=g-long-ternary


class ClassTest(unittest.TestCase):

  def setUp(self):
    super(ClassTest, self).setUp()
    tm = ast_pb2.Namemap()
    text_format.Parse("""
        name: "ImportedBase"
        fq_name: "path.python.Base"
      """, tm)
    self.m = pyext.Module(PATH, namemap=(tm,))
    self.code = (dict(tochar='PyUnicode_AsUTF8', f='',
                      frchar='PyUnicode_FromString') if self.m.py3output
                 else
                 dict(tochar='PyString_AS_STRING',
                      frchar='PyString_FromString',
                      f=' | Py_TPFLAGS_CHECKTYPES'))
    self.maxDiff = 100000  # pylint: disable=invalid-name

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
      cpp_has_trivial_dtor: true
      members {
        decltype: CONST
        const {
          name {
            native: "S"
            cpp_name: "kS"
          }
          type {
            lang_type: "str"
            cpp_type: "const char*"
          }
        }
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
        ::clif::Instance<StructTy> cpp;
        PyObject* weakrefs = nullptr;
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

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructTy";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_getset = Properties;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyDict_SetItemString(pyStruct::wrapper_Type->tp_dict, "S", Clif_PyObjFrom(static_cast<const char*>(kS), {})) < 0) goto err;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyDict_SetItemString(pyStruct::wrapper_Type->tp_dict, "S", Clif_PyObjFrom(static_cast<const char*>(kS), {})) < 0) goto err;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
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
        ::clif::Instance<StructTy> cpp;
        PyObject* weakrefs = nullptr;
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

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("as_Base_Foo_ptr_constBar_ref"), (PyCFunction)as_Base_Foo_ptr_constBar_ref, METH_NOARGS, C("Upcast to ::Base<Foo*, const Bar&>*")},
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        Py_BEGIN_ALLOW_THREADS
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_END_ALLOW_THREADS
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructTy";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_getset = Properties;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testPythonImportedDerivedStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructTy"
      }
      bases {
        native: "ImportedBase"
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
        ::clif::Instance<StructTy> cpp;
        PyObject* weakrefs = nullptr;
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

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        Py_BEGIN_ALLOW_THREADS
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_END_ALLOW_THREADS
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructTy";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_getset = Properties;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        PyObject* base_cls = ImportFQName("path.python.Base");
        if (base_cls == nullptr) return false;
        if (!PyObject_TypeCheck(base_cls, &PyType_Type)) {
          Py_DECREF(base_cls);
          PyErr_SetString(PyExc_TypeError, "Base class path.python.Base is not a new style class inheriting from object.");
          return false;
        }
        pyStruct::wrapper_Type->tp_base = reinterpret_cast<PyTypeObject*>(base_cls);
        // Check that base_cls is a *statically* allocated PyType.
        if (pyStruct::wrapper_Type->tp_base->tp_alloc == PyType_GenericAlloc) {
          Py_DECREF(base_cls);
          PyErr_SetString(PyExc_TypeError, "Base class path.python.Base is a dynamic (Python defined) class.");
          return false;
        }
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
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
      cpp_has_trivial_dtor: true
      members {
        decltype: CLASS
        class_ {
          name {
            native: "Inner"
            cpp_name: "OutKlass::InnKlass"
          }
          cpp_has_trivial_dtor: true
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
        ::clif::Instance<OutKlass> cpp;
        PyObject* weakrefs = nullptr;
      };

      static OutKlass* ThisPtr(PyObject*);

      namespace pyInner {

      struct wrapper {
        PyObject_HEAD
        ::clif::Instance<OutKlass::InnKlass> cpp;
        PyObject* weakrefs = nullptr;
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
        PyObject *py_enum_class = nullptr;
        PyObject *modname = nullptr;
        PyObject *py = nullptr;
        PyObject *names = PyTuple_New(1);
        if (names == nullptr) return nullptr;
        if ((py = Py_BuildValue("(NN)", %(frchar)s("A"), PyInt_FromLong(
              static_cast<typename std::underlying_type<OutKlass::InnKlass::X>::type>(OutKlass::InnKlass::X::A)))
            ) == nullptr) goto err;
        PyTuple_SET_ITEM(names, 0, py);
        py = %(frchar)s("Outer.Inner.X");
        if (py == nullptr) {
          goto err;
        }
        modname = %(frchar)s(ThisModuleName);
        if (modname == nullptr) {
          goto err;
        }
        py_enum_class = PyObject_CallFunctionObjArgs(_IntEnum, py, names, nullptr);
        if (py_enum_class != nullptr) {
          PyObject_SetAttrString(py_enum_class, "__module__", modname);
        }
      err:
        Py_XDECREF(modname);
        Py_XDECREF(py);
        Py_XDECREF(names);
        return py_enum_class;
      }

      static PyObject* _X{};  // set by above func in Init()

      static PyGetSetDef Properties[] = {
        {C("i"), get_i, set_i, C("C++ bool OutKlass::InnKlass.i")},
        {}
      };

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Inner __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Inner __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Inner __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Outer.Inner");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Outer.Inner";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for OutKlass::InnKlass";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_getset = Properties;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Inner takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<OutKlass::InnKlass>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static OutKlass::InnKlass* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_OutKlass_InnKlass"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to OutKlass::InnKlass*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyInner

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Outer __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Outer __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Outer __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Outer");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Outer";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for OutKlass";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Outer takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<OutKlass>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static OutKlass* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_OutKlass"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to OutKlass*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyOuter
    """ % self.code, """
      bool Ready() {
        pyOuter::pyInner::wrapper_Type =
        pyOuter::pyInner::_build_heap_type();
        if (PyType_Ready(pyOuter::pyInner::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyOuter::pyInner::wrapper_Type, "__module__", modname);
        Py_INCREF(pyOuter::pyInner::wrapper_Type);  // For PyModule_AddObject to steal.
        pyOuter::wrapper_Type =
        pyOuter::_build_heap_type();
        if (PyType_Ready(pyOuter::wrapper_Type) < 0) return false;
        PyObject_SetAttrString((PyObject *) pyOuter::wrapper_Type, "__module__", modname);
        Py_INCREF(pyOuter::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
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
        if (PyDict_SetItemString(pyOuter::pyInner::wrapper_Type->tp_dict, "X", (pyOuter::pyInner::_X=pyOuter::pyInner::wrapX())) < 0) goto err;
        if (PyDict_SetItemString(pyOuter::wrapper_Type->tp_dict, "Inner", reinterpret_cast<PyObject*>(pyOuter::pyInner::wrapper_Type)) < 0) goto err;
        if (PyModule_AddObject(module, "Outer", reinterpret_cast<PyObject*>(pyOuter::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
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
        if (PyDict_SetItemString(pyOuter::pyInner::wrapper_Type->tp_dict, "X", (pyOuter::pyInner::_X=pyOuter::pyInner::wrapX())) < 0) goto err;
        if (PyDict_SetItemString(pyOuter::wrapper_Type->tp_dict, "Inner", reinterpret_cast<PyObject*>(pyOuter::pyInner::wrapper_Type)) < 0) goto err;
        if (PyModule_AddObject(module, "Outer", reinterpret_cast<PyObject*>(pyOuter::wrapper_Type)) < 0) goto err;
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
      cpp_has_trivial_dtor: true
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
        ::clif::Instance<StructTy> cpp;
        PyObject* weakrefs = nullptr;
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

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructTy";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_getset = Properties;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
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
      cpp_has_trivial_dtor: true
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
        ::clif::Instance<StructTy> cpp;
        PyObject* weakrefs = nullptr;
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

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("get_a"), (PyCFunction)get_a, METH_NOARGS, C("get_a()->int  C++ StructTy.a getter")},
        {C("set_a"), set_a, METH_O, C("set_a(int)  C++ StructTy.a setter")},
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructTy";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructTy"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructTy*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
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
      cpp_has_trivial_dtor: true
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
        ::clif::Instance<StructTy> cpp;
        PyObject* weakrefs = nullptr;
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

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructTy";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_getset = Properties;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructTy>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructTy* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testFinalStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructCpp"
      }
      final: true
      cpp_has_trivial_dtor: true
      members {
        decltype: FUNC
        func {
          py_keep_gil: true
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
        ::clif::Instance<StructCpp> cpp;
        PyObject* weakrefs = nullptr;
      };

      // f()
      static PyObject* wrapf(PyObject* self) {
        // Call actual C++ method.
        reinterpret_cast<wrapper*>(self)->cpp->f();
        Py_RETURN_NONE;
      }

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("f"), (PyCFunction)wrapf, METH_NOARGS, C("f()\n  Calls C++ function\n  void f()")},
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructCpp";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructCpp>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructCpp* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
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

      struct Overrider : StructCpp, PyObjRef {
        using StructCpp::StructCpp;

        void f() override {
          SafeAttr impl(self(), "F");
          if (impl.get()) {
            ::clif::callback::Func<void>(impl.get(), {})();
          } else {
            ::StructCpp::f();
          }
        }
      };

      struct wrapper {
        PyObject_HEAD
        ::clif::Instance<Overrider> cpp;
        PyObject* weakrefs = nullptr;
      };

      static StructCpp* ThisPtr(PyObject*);

      // F()
      static PyObject* wrapf_as_F(PyObject* self) {
        // Call actual C++ method.
        StructCpp* c = ThisPtr(self);
        if (!c) return nullptr;
        PyThreadState* _save;
        Py_UNBLOCK_THREADS
        c->StructCpp::f();
        Py_BLOCK_THREADS
        Py_RETURN_NONE;
      }

      // Implicit cast this as StructCpp*
      static PyObject* as_StructCpp(PyObject* self) {
        StructCpp* p = ::clif::python::Get(reinterpret_cast<wrapper*>(self)->cpp);
        if (p == nullptr) return nullptr;
        return PyCapsule_New(p, C("StructCpp"), nullptr);
      }

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("F"), (PyCFunction)wrapf_as_F, METH_NOARGS, C("F()\n  Calls C++ function\n  void ::StructCpp::f()")},
        {C("as_StructCpp"), (PyCFunction)as_StructCpp, METH_NOARGS, C("Upcast to StructCpp*")},
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        Py_BEGIN_ALLOW_THREADS
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_END_ALLOW_THREADS
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructCpp";
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<Overrider>();
        reinterpret_cast<wrapper*>(self)->cpp->::clif::PyObjRef::Init(self);
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructCpp* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructCpp"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructCpp*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        return nullptr;
      }
    """))

  def testIteratorStruct(self):
    self.assertClassEqual("""
      name {
        native: "Struct"
        cpp_name: "StructCpp"
      }
      cpp_has_trivial_dtor: true
      members {
        decltype: CLASS
        class_ {
          cpp_has_trivial_dtor: true
          name {
            native: "__iter__"
            cpp_name: "iterator"
          }
          members {
            decltype: FUNC
            func {
              name {
                native: "__next__"
                cpp_name: "operator*"
              }
              returns {
                type {
                  lang_type: "int"
                  cpp_type: "int"
                }
              }
            }
          }
        }
      }
    """, r"""
      namespace pyStruct {

      struct wrapper {
        PyObject_HEAD
        ::clif::Instance<StructCpp> cpp;
        PyObject* weakrefs = nullptr;
      };

      namespace py__iter__ {
      typedef ::clif::Iterator<StructCpp, iterator> iterator;
      }

      static StructCpp* ThisPtr(PyObject*);

      namespace py__iter__ {

      struct wrapper {
        PyObject_HEAD
        iterator iter;
      };

      PyObject* iternext(PyObject* self) {
        PyThreadState* _save;
        Py_UNBLOCK_THREADS
        auto* v = reinterpret_cast<wrapper*>(self)->iter.Next();
        Py_BLOCK_THREADS
        return v? Clif_PyObjFrom(*v, {}): nullptr;
      }

      // __iter__ __del__
      static void _dtor(PyObject* self) {
        Py_BEGIN_ALLOW_THREADS
        reinterpret_cast<wrapper*>(self)->iter.~iterator();
        Py_END_ALLOW_THREADS
        Py_TYPE(self)->tp_free(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct.__iter__");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct.__iter__";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for iterator";
        ty->tp_iter = PyObject_SelfIter;
        ty->tp_iternext = iternext;
        ty->tp_init = Clif_PyType_Inconstructible;
        return ty;
      }

      }  // namespace py__iter__

      PyObject* new_iter(PyObject* self) {
        if (!ThisPtr(self)) return nullptr;
        py__iter__::wrapper* it = PyObject_New(py__iter__::wrapper, py__iter__::wrapper_Type);
        if (!it) return nullptr;
        using std::equal_to;  // Often a default template argument.
        new(&it->iter) py__iter__::iterator(MakeStdShared(reinterpret_cast<wrapper*>(self)->cpp));
        return reinterpret_cast<PyObject*>(it);
      }

      static PyMethodDef MethodsStaticAlloc[] = {
        {C("__reduce_ex__"), (PyCFunction)::clif::ReduceExImpl, METH_VARARGS | METH_KEYWORDS, C("Helper for pickle.")},
        {}
      };

      // Struct __init__
      static int _ctor(PyObject* self, PyObject* args, PyObject* kw);

      // Struct __new__
      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems);

      // Struct __del__
      static void _dtor(PyObject* self) {
        if (reinterpret_cast<wrapper*>(self)->weakrefs) {
          PyObject_ClearWeakRefs(self);
        }
        reinterpret_cast<wrapper*>(self)->cpp.Destruct();
        Py_TYPE(self)->tp_free(self);
      }

      static void _del(void* self) {
        delete reinterpret_cast<wrapper*>(self);
      }

      PyTypeObject* wrapper_Type = nullptr;

      static PyTypeObject* _build_heap_type() {
        PyHeapTypeObject *heap_type =
            (PyHeapTypeObject *) PyType_Type.tp_alloc(&PyType_Type, 0);
        if (!heap_type)
          return nullptr;
        heap_type->ht_name = (PyObject *) PyString_FromString(
            "Struct");
        PyTypeObject *ty = &heap_type->ht_type;
        ty->tp_as_number = &heap_type->as_number;
        ty->tp_as_sequence = &heap_type->as_sequence;
        ty->tp_as_mapping = &heap_type->as_mapping;
      #if PY_VERSION_HEX >= 0x03050000
        ty->tp_as_async = &heap_type->as_async;
      #endif
        ty->tp_name = "path.to.ext.module.test.Struct";
        ty->tp_basicsize = sizeof(wrapper);
        ty->tp_dealloc = _dtor;
        ty->tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HEAPTYPE;
        ty->tp_doc = "CLIF wrapper for StructCpp";
        ty->tp_iter = new_iter;
        ty->tp_methods = MethodsStaticAlloc;
        ty->tp_init = _ctor;
        ty->tp_alloc = _new;
        ty->tp_new = PyType_GenericNew;
        ty->tp_free = _del;
        ty->tp_weaklistoffset = offsetof(wrapper, weakrefs);
        return ty;
      }

      static int _ctor(PyObject* self, PyObject* args, PyObject* kw) {
        if ((args && PyTuple_GET_SIZE(args) != 0) || (kw && PyDict_Size(kw) != 0)) {
          PyErr_SetString(PyExc_TypeError, "Struct takes no arguments");
          return -1;
        }
        reinterpret_cast<wrapper*>(self)->cpp = ::clif::MakeShared<StructCpp>();
        return 0;
      }

      static PyObject* _new(PyTypeObject* type, Py_ssize_t nitems) {
        DCHECK(nitems == 0);
        wrapper* wobj = new wrapper;
        PyObject* self = reinterpret_cast<PyObject*>(wobj);
        return PyObject_Init(self, wrapper_Type);
      }

      static StructCpp* ThisPtr(PyObject* py) {
        if (Py_TYPE(py) == wrapper_Type) {
          return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
        }
        PyObject* base = PyObject_CallMethod(py, C("as_StructCpp"), nullptr);
        if (base == nullptr) {
          PyErr_Clear();
        } else {
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
        if (PyObject_IsInstance(py, reinterpret_cast<PyObject*>(wrapper_Type))) {
          if (!base) {
            return ::clif::python::Get(reinterpret_cast<wrapper*>(py)->cpp);
          }
          PyErr_Format(PyExc_ValueError, "can't convert %%s %%s to StructCpp*", ClassName(py), ClassType(py));
        } else {
          PyErr_Format(PyExc_TypeError, "expecting %%s instance, got %%s %%s", wrapper_Type->tp_name, ClassName(py), ClassType(py));
        }
        return nullptr;
      }

      }  // namespace pyStruct
    """ % self.code, """
      bool Ready() {
        pyStruct::py__iter__::wrapper_Type =
        pyStruct::py__iter__::_build_heap_type();
        if (PyType_Ready(pyStruct::py__iter__::wrapper_Type) < 0) return false;
        PyObject *modname = PyString_FromString(ThisModuleName);
        if (modname == nullptr) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::py__iter__::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::py__iter__::wrapper_Type);  // For PyModule_AddObject to steal.
        pyStruct::wrapper_Type =
        pyStruct::_build_heap_type();
        if (PyType_Ready(pyStruct::wrapper_Type) < 0) return false;
        PyObject_SetAttrString((PyObject *) pyStruct::wrapper_Type, "__module__", modname);
        Py_INCREF(pyStruct::wrapper_Type);  // For PyModule_AddObject to steal.
        return true;
      }
    """ + ("""
      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
        "CLIF-generated module for test.h", // module doc
        -1,  // module keeps state in global variables
        nullptr
      };

      PyObject* Init() {
        PyObject* module = PyModule_Create(&Module);
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
        return module;
      err:
        Py_DECREF(module);
        return nullptr;
      }
    """ if self.m.py3output else """
      PyObject* Init() {
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
        if (!module) return nullptr;
        if (PyModule_AddObject(module, "Struct", reinterpret_cast<PyObject*>(pyStruct::wrapper_Type)) < 0) goto err;
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
        PyObject *py_enum_class = nullptr;
        PyObject *modname = nullptr;
        PyObject *py = nullptr;
        PyObject *names = PyTuple_New(2);
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
        if (py == nullptr) {
          goto err;
        }
        modname = %(frchar)s(ThisModuleName);
        if (modname == nullptr) {
          goto err;
        }
        py_enum_class = PyObject_CallFunctionObjArgs(_IntEnum, py, names, nullptr);
        if (py_enum_class != nullptr) {
          PyObject_SetAttrString(py_enum_class, "__module__", modname);
        }
      err:
        Py_XDECREF(modname);
        Py_XDECREF(py);
        Py_XDECREF(names);
        return py_enum_class;
      }

      static PyObject* _MyEnum{};  // set by above func in Init()
    """ % self.code, """
      bool Ready() {
        return true;
      }

      static struct PyModuleDef Module = {
        PyModuleDef_HEAD_INIT,
        ThisModuleName,  // module name
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
        PyObject* module = Py_InitModule3(ThisModuleName, nullptr, "CLIF-generated module for test.h");
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
