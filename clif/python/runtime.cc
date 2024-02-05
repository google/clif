// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "clif/python/runtime.h"

#include <Python.h>
#include <stdio.h>

#include <cassert>
#include <cstdint>
#include <cstring>
#include <functional>
#include <initializer_list>
#include <string>
#include <system_error>  // NOLINT(build/c++11)
#include <utility>

#include "absl/container/flat_hash_map.h"
#include "absl/log/check.h"
#include "absl/log/log.h"
#include "clif/python/pickle_support.h"
#include "clif/python/stltypes.h"

extern "C"
int Clif_PyType_Inconstructible(PyObject* self, PyObject* a, PyObject* kw) {
  PyErr_Format(PyExc_TypeError, "%s: No constructor defined!",
               Py_TYPE(self)->tp_name);
  return -1;
}

namespace clif {

void SetErrorWrappedTypeCannotBeUsedAsBase(PyTypeObject* wrapper_type,
                                           PyTypeObject* derived_type) {
  std::string derived_type_module;
  PyObject* mod_attr =
      PyObject_GetAttrString((PyObject*)derived_type, "__module__");
  if (mod_attr == nullptr) {
    PyErr_Clear();
  } else {
    // Report but clear all unexpected low-level errors.
    if (!PyUnicode_Check(mod_attr)) {
      derived_type_module = "<PyUnicode_Check(__module__) FALSE>";
    } else {
      Py_ssize_t length;
      const char* data = PyUnicode_AsUTF8AndSize(mod_attr, &length);
      if (PyErr_Occurred()) {
        PyErr_Clear();
        derived_type_module = "<PyUnicode_AsUTF8AndSize(__module__) ERROR>";
      } else {
        derived_type_module = std::string(data, length);
      }
    }
    Py_DECREF(mod_attr);
    derived_type_module += ".";
  }
  PyErr_Format(PyExc_TypeError,
               "%s cannot be used as a base class for a Python type because it "
               "has no constructor defined (the derived type is %s%s).",
               wrapper_type->tp_name, derived_type_module.c_str(),
               derived_type->tp_name);
}

void PyObjRef::Init(PyObject* self) {
  self_ = PyWeakref_NewRef(self, nullptr);
  // We don't care about non-weakrefencable objects (most likely the
  // CLIF-generated wrapper object), so nullptr is fine, just clear the error.
  PyErr_Clear();
}

void PyObjRef::HoldPyObj(PyObject* self) {
  pyowner_ = self;
  Py_INCREF(pyowner_);
}
void PyObjRef::DropPyObj() {
  Py_CLEAR(pyowner_);
}

PyObject* PyObjRef::PoisonPill() const {
  // Memory pattern mnemonic is _______CallInit.
  return reinterpret_cast<PyObject*>(0xCA771417);
}

PyObject* PyObjRef::self() const {
  if (self_ == nullptr) return nullptr;
  PyGILState_STATE threadstate = PyGILState_Ensure();
  PyObject* py = PyWeakref_GetObject(self_);
  if (py == Py_None) py = nullptr;
  Py_XINCREF(py);
  PyGILState_Release(threadstate);
  return py;
}

PyObjRef::~PyObjRef() {
  PyGILState_STATE threadstate = PyGILState_Ensure();
  Py_CLEAR(pyowner_);
  Py_CLEAR(self_);
  PyGILState_Release(threadstate);
}

SafePyObject::~SafePyObject() {
  if (py_) {
    PyGILState_STATE threadstate = PyGILState_Ensure();
    Py_DECREF(py_);
    PyGILState_Release(threadstate);
  }
}

// Resource management for virtual override methods.
SafeAttr::SafeAttr(PyObject* pyobj, const char* name) {
  state_ = PyGILState_Ensure();
  meth_ = pyobj ? PyObject_GetAttrString(pyobj, name) : nullptr;
  Py_XDECREF(pyobj);  // Assume that method descriptor keeps the obj alive.
  if (meth_ == nullptr) {
    if (PyErr_ExceptionMatches(PyExc_AttributeError)) {
      PyErr_Clear();
    } else {
      LogFatalIfPythonErrorOccurred();
    }
    PyGILState_Release(state_);
  }
}
SafeAttr::~SafeAttr() {
  if (meth_ != nullptr) {
    Py_DECREF(meth_);
    PyGILState_Release(state_);
  }
}

int ClearImportCache(PyObject* module) {
  return 0;
}

// Given full.path.to.a.module.Name import module and return Name from module.
PyObject* ImportFQName(const std::string& full_class_name) {
  // Split full_class_name at the last dot.
  auto last_dot = full_class_name.find_last_of('.');
  if (last_dot == std::string::npos) {
    PyErr_Format(PyExc_ValueError, "No dot in full_class_name '%s'",
                 full_class_name.c_str());
    return nullptr;
  }
  PyObject* module = PyImport_ImportModule(
      full_class_name.substr(0, last_dot).c_str());
  if (!module) return nullptr;
  PyObject* py = PyObject_GetAttrString(
      module, full_class_name.substr(last_dot+1).c_str());
  Py_DECREF(module);
  return py;
}

// Given full.path.to.a.module.Name.A.B, and toplevel class name
// full.path.to.a.module.Name, import Name from module, and return Name.A.B.
PyObject* ImportFQName(const std::string& full_class_name,
                       const std::string& toplevel_class_name) {
  if (full_class_name == toplevel_class_name || toplevel_class_name.empty()) {
    return ImportFQName(toplevel_class_name);
  }
  if (full_class_name.rfind(toplevel_class_name + ".", 0) != 0) {
    PyErr_Format(
        PyExc_ValueError,
        "toplevel class name '%s' is not a prefix of full_class_name '%s'",
        toplevel_class_name.c_str(), full_class_name.c_str());
    return nullptr;
  }
  PyObject* py = ImportFQName(toplevel_class_name);
  auto dot = full_class_name.find_first_of('.', toplevel_class_name.size());
  while (dot != std::string::npos) {
    const auto name = dot + 1;
    const auto next_dot = full_class_name.find_first_of('.', name);
    const auto len =
        (next_dot != std::string::npos) ? next_dot - name : std::string::npos;
    const auto attr_name = full_class_name.substr(name, len);
    if (len == 0) {
      Py_DECREF(py);
      PyErr_Format(PyExc_ValueError,
                   "name '%s' is not a valid fully qualified class name",
                   full_class_name.c_str());
      return nullptr;
    }
    PyObject* next = PyObject_GetAttrString(py, attr_name.c_str());
    Py_DECREF(py);
    if (next == nullptr) {
      return nullptr;
    }
    py = next;
    dot = next_dot;
  }
  return py;
}

// py.__class__.__name__
const char* ClassName(PyObject* py) {
  if (PyType_Check(py)) {
    return reinterpret_cast<PyTypeObject*>(py)->tp_name;
  }
  return Py_TYPE(py)->tp_name;
}

// type(py) renamed from {classobj, instance, type, class X}
const char* ClassType(PyObject* py) {
  if (PyType_Check(py)) {
    return "class";
  }
  return "instance";
}

bool CallableNeedsNarguments(PyObject* callable, int nargs) {
  PyObject* getcallargs = ImportFQName("inspect.getcallargs");
  if (!getcallargs) return false;
  PyObject* args = PyTuple_New(nargs+1);
  Py_INCREF(callable);
  PyTuple_SET_ITEM(args, 0, callable);
  for (int i=1; i <= nargs; ++i) {
    Py_INCREF(Py_None);
    PyTuple_SET_ITEM(args, i, Py_None);
  }
  PyObject* binded = PyObject_CallObject(getcallargs, args);
  Py_DECREF(getcallargs);
  Py_DECREF(args);
  if (!binded) return false;  // PyExc_TypeError is set.
  // explicitly clear references to give to garbage collector more information
  // this potentially can cause faster collecting of unused objects
  PyDict_Clear(binded);
  Py_DECREF(binded);
  return true;
}

PyObject* DefaultArgMissedError(const char func[], const char* argname) {
  PyErr_Format(PyExc_ValueError, "%s() argument %s needs a non-default value",
               func, argname);
  return nullptr;
}

PyObject* ArgError(const char func[],
                   const char* argname,
                   const char ctype[],
                   PyObject* arg) {
  PyObject* exc = PyErr_Occurred();
  if (exc == nullptr) {
    PyErr_Format(
        PyExc_TypeError, "%s() argument %s is not valid for %s (%s %s given)",
        func, argname, ctype, ClassName(arg), ClassType(arg));
  } else if (exc == PyExc_TypeError) {
    PyErr_Format(
        exc, "%s() argument %s is not valid for %s (%s %s given): %s",
        func, argname, ctype, ClassName(arg), ClassType(arg),
        python::ExcStr(false).c_str());
  } else {
    PyErr_Format(
        exc, "%s() argument %s is not valid: %s",
        func, argname, python::ExcStr(false).c_str());
  }
  return nullptr;
}

namespace python {

namespace {

int FilterMockUsingPragmaticHeuristics(PyObject* inst) {
  // Definition of the class variable leveraged as "is a mock" indicator:
  // https://github.com/python/cpython/blob/7d41ead9191a18bc473534f6f8bd1095f2232cc2/Lib/unittest/mock.py#L426
  // The runtime overhead is very small: a single attribute lookup.
  // Likelihood of false negatives: practically zero.
  // Likelihood of false positives: extremely unlikely.
  // It actually seems much more likely that this function works as intended
  // for hypothetical non-unittest mocks, rather than producing a false
  // positive for an object that is not a mock.
  assert(PyType_Check(inst) == 0);
  PyTypeObject* typ = reinterpret_cast<PyTypeObject*>(Py_TYPE(inst));
  PyObject* mock_attr = PyObject_GetAttrString(reinterpret_cast<PyObject*>(typ),
                                               "_mock_return_value");
  if (mock_attr != nullptr) {
    Py_DECREF(mock_attr);
    return 0;  // "Yes this is a mock."
  }
  if (PyErr_ExceptionMatches(PyExc_AttributeError)) {
    PyErr_Clear();
    return 1;  // "No this is not a mock."
  }
  return -1;  // Unexpected error.
}

}  // namespace

int IsWrapperTypeInstance(PyObject* inst, PyTypeObject* cls) {
  int stat = PyObject_IsInstance(inst, reinterpret_cast<PyObject*>(cls));
  if (stat == 1) {
    return FilterMockUsingPragmaticHeuristics(inst);
  }
  return stat;
}

std::string ExcStr(bool add_type) {
  PyObject* exc, *val, *tb;
  PyErr_Fetch(&exc, &val, &tb);
  if (!exc) return "";
  PyErr_NormalizeException(&exc, &val, &tb);
  std::string err;
  if (add_type) err = std::string(ClassName(exc)) + ": ";
  Py_DECREF(exc);
  if (val) {
    PyObject* val_str = PyObject_Str(val);
    Py_DECREF(val);
    if (val_str) {
      err += PyUnicode_AsUTF8(val_str);
      Py_DECREF(val_str);
    }
  }
  Py_XDECREF(tb);
  return err;
}

void ThrowExcStrIfCppExceptionsEnabled() {
#ifdef __EXCEPTIONS
  if (PyErr_Occurred()) throw std::domain_error(python::ExcStr());
  throw std::system_error(std::error_code(), "Python: exception not set");
#endif
}

namespace {

void DumpPyErrToStderr() {
  fprintf(stderr, "@BEGIN(Python exception)\n\n");
  fflush(stderr);
  PyErr_PrintEx(1);
  fprintf(stderr, "\n@END(Python exception)\n");
  fflush(stderr);
}

}  // namespace

void LogCallbackPythonError(PyObject* callable,
                            const char* return_typeid_name) {
  // This block must remain at top, to ensure that the Python error is not
  // clobbered:
  fflush(stdout);  // Possibly redundant, depending on behavior of LOG().
  fflush(stderr);  // But better safe than sorry.
  if (!PyErr_Occurred()) {
    LOG(FATAL)
        << "Python exception in call of clif::callback EXPECTED BUT NOT SET.";
  }
  LOG(ERROR) << "Python exception in call of clif::callback FOLLOWS (stderr):";
  DumpPyErrToStderr();

  LOG(ERROR) << "repr(callable) FOLLOWS (stderr):";
  fprintf(stderr, "@BEGIN(Python repr)\n\n");
  fflush(stderr);
  if (PyObject_Print(callable, stderr, 0) == -1) {
    fprintf(stderr, "\nFAILED: PyObject_Print()");
    fflush(stderr);
    PyErr_Clear();  // Ignore any errors from printing the exception.
  }
  fprintf(stderr, "\n\n@END(Python repr)\n");
  fflush(stderr);
  LOG(ERROR) << "typeid(ReturnType).name(): " << return_typeid_name
             << " [HINT: http://demangle]";
}

}  // namespace python

// The pyclif_instance_dict_* functions are heavily modified versions of
// pybind11 code:
// http://google3/third_party/pybind11/include/pybind11/detail/class.h?l=449&rcl=276599738
extern "C" PyObject* pyclif_instance_dict_get(PyObject* self, void*) {
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr == nullptr) {
    return nullptr;
  }
  if (*dictptr == nullptr) {
    *dictptr = PyDict_New();
  }
  Py_XINCREF(*dictptr);
  return *dictptr;
}

extern "C" int pyclif_instance_dict_set(
    PyObject* self, PyObject* new_dict, void*) {
  if (!PyDict_Check(new_dict)) {
    PyErr_Format(
        PyExc_TypeError, "__dict__ must be set to a dict, not a %s",
        Py_TYPE(new_dict)->tp_name);
    return -1;
  }
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr == nullptr) {
    PyErr_Format(
        PyExc_SystemError,
        "pyclif_instance_dict_set dictptr == nullptr for type %s",
        Py_TYPE(self)->tp_name);
    return -1;
  }
  Py_CLEAR(*dictptr);
  *dictptr = new_dict;
  Py_INCREF(*dictptr);
  return 0;
}

extern "C" int pyclif_instance_dict_traverse(
    PyObject *self, visitproc visit, void *arg) {
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr != nullptr) {
    Py_VISIT(*dictptr);
  }
  return 0;
}

extern "C" int pyclif_instance_dict_clear(PyObject *self) {
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr != nullptr) {
    Py_CLEAR(*dictptr);
  }
  return 0;
}

void pyclif_instance_dict_enable(PyTypeObject* ty, std::size_t dictoffset) {
  ty->tp_dictoffset = (Py_ssize_t) dictoffset;
  // Currently the generated tp_alloc, tp_new, tp_dealloc, tp_free code is
  // incompatible with garbage collection.
  // Note: clif/testing/python/enable_instance_dict_test.py
  // includes testReferenceCycle, which doubles as a reminder.
  // Envisioned future: when switching to generating pybind11 code, this code
  // will be obsolete and purged, testReferenceCycle will "break" and then
  // adjusted to exercise the behavior with GC enabled.
  // ty->tp_flags |= Py_TPFLAGS_HAVE_GC;
  // ty->tp_traverse = pyclif_instance_dict_traverse;
  // ty->tp_clear = pyclif_instance_dict_clear;
  // tp_getset generated by gen.GetSetDef().
}

bool ensure_no_args_and_kw_args(const char* func, PyObject* args,
                                PyObject* kw) {
  if (kw != nullptr) {
    PyErr_Format(PyExc_TypeError, "%s() takes no keyword arguments", func);
    return false;
  }
  if (args != nullptr) {
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    if (nargs != 0) {
      PyErr_Format(PyExc_TypeError, "%s() takes no arguments (%zd given)", func,
                   nargs);
      return false;
    }
  }
  return true;
}

PyObject* ReduceExImpl(PyObject* self, PyObject* args, PyObject* kw) {
  static const char* kwlist[] = {"protocol", nullptr};
  int protocol = -1;
  if (!PyArg_ParseTupleAndKeywords(args, kw, "|i:__reduce_ex__",
                                   const_cast<char**>(kwlist),
                                   &protocol)) {
    return nullptr;
  }
  return ReduceExCore(self, protocol);
}

namespace {

bool PyObjectIsInstanceWithOneOfTpNames(
    PyObject* obj, std::initializer_list<const char*> tp_names) {
  if (PyType_Check(obj)) {
    return false;
  }
  const char* obj_tp_name = Py_TYPE(obj)->tp_name;
  for (const auto* tp_name : tp_names) {
    if (strcmp(obj_tp_name, tp_name) == 0) {
      return true;
    }
  }
  return false;
}

}  // namespace

bool PyObjectTypeIsConvertibleToStdVector(PyObject* obj) {
  if (PySequence_Check(obj) != 0) {
    return !PyUnicode_Check(obj) && !PyBytes_Check(obj);
  }
  return (PyGen_Check(obj) != 0) || (PyAnySet_Check(obj) != 0) ||
         PyObjectIsInstanceWithOneOfTpNames(
             obj, {"dict_keys", "dict_values", "dict_items", "map", "zip"});
}

bool PyObjectTypeIsConvertibleToStdSet(PyObject* obj) {
  return (PyAnySet_Check(obj) != 0) ||
         PyObjectIsInstanceWithOneOfTpNames(obj, {"dict_keys"});
}

bool PyObjectTypeIsConvertibleToStdMap(PyObject* obj) {
  if (PyDict_Check(obj)) {
    return true;
  }
  // Implicit requirement in the conditions below:
  // A type with `.__getitem__()` & `.items()` methods must implement these
  // to be compatible with https://docs.python.org/3/c-api/mapping.html
  if (PyMapping_Check(obj) == 0) {
    return false;
  }
  PyObject* items = PyObject_GetAttrString(obj, "items");
  if (items == nullptr) {
    PyErr_Clear();
    return false;
  }
  bool is_convertible = (PyCallable_Check(items) != 0);
  Py_DECREF(items);
  return is_convertible;
}

void LogFatalIfPythonErrorOccurred() {
  if (PyErr_Occurred()) {
    LOG(ERROR) << "UNEXPECTED Python exception FOLLOWS (stderr):";
    python::DumpPyErrToStderr();
    LOG(FATAL) << "UNEXPECTED PyErr_Occurred(): The unexpected Python error "
                  "was sent to stderr.";
  }
}

void SetIsNotConvertibleError(PyObject* py_obj, const char* cpp_type) {
  LogFatalIfPythonErrorOccurred();
  PyErr_Format(PyExc_TypeError, "%s %s is not convertible to a %s object",
               ClassName(py_obj), ClassType(py_obj), cpp_type);
}

namespace {

bool SetPyClifCodeGenMode(PyObject* module, const char* codegen_mode) {
  PyObject* codegen_mode_py = PyUnicode_FromString(codegen_mode);
  if (codegen_mode_py == nullptr) {
    return false;
  }
  int stat = PyObject_SetAttrString(module, "__pyclif_codegen_mode__",
                                    codegen_mode_py);
  Py_DECREF(codegen_mode_py);
  return (stat == 0);
}

}  // namespace

PyObject* ModuleCreateAndSetPyClifCodeGenMode(PyModuleDef* module_def) {
  PyObject* module = PyModule_Create(module_def);
  if (!module) return nullptr;
  if (!SetPyClifCodeGenMode(module, "c_api")) {
    Py_DECREF(module);
    return nullptr;
  }
  return module;
}

namespace {

extern "C" PyObject* FunctionCapsuleOneArgPyCFunction(PyObject* cap,
                                                      PyObject* arg) {
  using function_type = std::function<void(PyObject*)>;
  void* fp = PyCapsule_GetPointer(cap, typeid(function_type).name());
  if (fp == nullptr) {
    return nullptr;
  }
  (*static_cast<function_type*>(fp))(arg);
  Py_RETURN_NONE;
}

static PyMethodDef FunctionCapsuleOneArgPyMethodDef = {
    "", FunctionCapsuleOneArgPyCFunction, METH_O, nullptr};

}  // namespace

PyObject* tp_new_impl_with_tp_init_safety_checks(
    PyTypeObject* type, PyObject* args, PyObject* kwds,
    derived_tp_init_registry_type* derived_tp_init_registry,
    initproc tp_init_impl, initproc tp_init_with_safety_checks) {
  if (type->tp_init != tp_init_impl &&
      type->tp_init != tp_init_with_safety_checks &&
      derived_tp_init_registry->count(type) == 0) {
    PyObject* wr_cb_fc = FunctionCapsule(
        std::function([type, derived_tp_init_registry](PyObject* wr) {
          CHECK_EQ(PyWeakref_CheckRef(wr), 1);
          auto num_erased = derived_tp_init_registry->erase(type);
          CHECK_EQ(num_erased, 1);
          Py_DECREF(wr);
        }));
    if (wr_cb_fc == nullptr) {
      return nullptr;
    }
    PyObject* wr_cb =
        PyCFunction_New(&FunctionCapsuleOneArgPyMethodDef, wr_cb_fc);
    Py_DECREF(wr_cb_fc);
    if (wr_cb == nullptr) {
      return nullptr;
    }
    PyObject* wr = PyWeakref_NewRef((PyObject*)type, wr_cb);
    Py_DECREF(wr_cb);
    if (wr == nullptr) {
      return nullptr;
    }
    CHECK_NE(wr, Py_None);
    (*derived_tp_init_registry)[type] = type->tp_init;
    type->tp_init = tp_init_with_safety_checks;
  }
  return PyType_GenericNew(type, args, kwds);
}

}  // namespace clif
