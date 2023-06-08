/*
 * Copyright 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef CLIF_PYTHON_RUNTIME_H_
#define CLIF_PYTHON_RUNTIME_H_

/*
From .../python-2.7.3-docs-html/c-api/intro.html#include-files:
Since Python may define some pre-processor definitions which affect the
standard headers on some systems, you must include Python.h before any standard
headers are included.
*/
#include <Python.h>
#include <string>
#include "clif/python/instance.h"
using std::string;

extern "C" int Clif_PyType_Inconstructible(PyObject*, PyObject*, PyObject*);

namespace clif {
namespace python {

std::string ExcStr(bool add_type = true);
void ThrowExcStrIfCppExceptionsEnabled();
void LogCallbackPythonError(PyObject* callable, const char* return_typeid_name);

template <typename T>
T* Get(const clif::Instance<T>& cpp, bool set_err = true) {
  T* d = cpp.get();
  if (set_err && d == nullptr) {
    PyErr_Format(PyExc_ValueError,
                 "Missing value for wrapped C++ type `%s`. "
                 "Potential root causes: "
                 "original value captured by std::unique_ptr; "
                 "or missing call of base class __init__.",
                 typeid(T).name());
  }
  return d;
}
}  // namespace python

// Returns py.__class__.__name__ (needed for PY2 old style classes).
const char* ClassName(PyObject* py);
const char* ClassType(PyObject* py);

// Load the base Python class.
PyObject* ImportFQName(const std::string& full_class_name);
PyObject* ImportFQName(const std::string& full_class_name,
                       const std::string& toplevel_class_name);
int ClearImportCache(PyObject*);

// Ensure we have enough args for callable.
bool CallableNeedsNarguments(PyObject* callable, int nargs);

// Format function argument missed error.
PyObject* DefaultArgMissedError(const char func[], const char* argname);

// Format function argument [conversion] error.
PyObject* ArgError(const char func[], const char* argname, const char ctype[],
                   PyObject* arg);

// RAII pyobj attribute holder with GIL management for virtual override methods.
class SafeAttr {
 public:
  SafeAttr(PyObject* pyobj, const char* name);  // Acquires GIL.
  ~SafeAttr();                                  // Releases GIL.
  SafeAttr(const SafeAttr& other) = delete;
  SafeAttr& operator=(const SafeAttr& other) = delete;
  SafeAttr(SafeAttr&& other) = delete;
  SafeAttr& operator=(SafeAttr&& other) = delete;

  PyObject* get() const { return meth_; }

 private:
  PyGILState_STATE state_;
  PyObject* meth_;
};

// RAII PyObject ownership and GIL safe to call from a C++ object.
class SafePyObject {
 public:
  // SafePyObject is implicitly convertible from PyObject*.
  explicit SafePyObject(PyObject* py) : py_(py) { Py_XINCREF(py); }
  ~SafePyObject();  // Grab GIL to do XDECREF.
  // Copy/move disabled to avoid extra inc/dec-refs (decref can be costly).
  SafePyObject(const SafePyObject& other) = delete;
  SafePyObject& operator=(const SafePyObject& other) = delete;
  SafePyObject(SafePyObject&& other) = delete;
  SafePyObject& operator=(SafePyObject&& other) = delete;
 private:
  PyObject* py_;
};

// When we share a C++ instance to a shared_ptr<T> C++ consumer, we need to make
// sure that its owner implementing virtual functions (Python object) will not
// go away or leak and keep ownership while we use it.
template<typename T>
struct SharedVirtual {
  // If Instance has 2+ owners it can't renounce ownership to an unique_ptr.
  Instance<T> prevent_ownership_renouncing;
  SafePyObject owner;

  SharedVirtual() = default;
  SharedVirtual(Instance<T> shared, PyObject* py)
      : prevent_ownership_renouncing(std::move(shared)), owner(py) {}
};

// Return the shared U* as a T*, which may be a different type.
template<typename T, typename U>
std::shared_ptr<T> MakeSharedVirtual(Instance<U> cpp, PyObject* py) {
  T* ptr = cpp.get();
  auto helper = std::make_shared<SharedVirtual<U>>(std::move(cpp), py);
  return std::shared_ptr<T>(helper, ptr);
}

// PyObject* "self" storage mixin for virtual method overrides.
// It weakrefs back to "self" to get the virtual method object.
// Also if C++ instance memory ownership moved to C++ code, it owns the "self"
// object.
// TODO: Create a shared __dict__ copy of 'self' that will not lose
// the C++ pointer after the normal 'self' renounced ownership, for potential
// use in virtual method run. Currently 'self' can't access C++ class content
// after it renounced ownership.
class PyObjRef {
 public:
#ifndef NDEBUG
  // Create a poison pill to check that Init() called for all instances.
  PyObjRef() : self_(PoisonPill()) {}
#else
  PyObjRef() = default;
#endif
  // This class is copy/movable but never used alone, only with some user class:
  //   class Overrider : public PyObjRef, public UserClass { ... }
  // and only instantiated from Python so those defs are not very useful.
  PyObjRef(const PyObjRef& other) = default;
  PyObjRef& operator=(const PyObjRef& other) = default;
  PyObjRef(PyObjRef&& other) = default;
  PyObjRef& operator=(PyObjRef&& other) = default;

  // Needed to clear the held Python references.
  virtual ~PyObjRef();

  // Keep a (weak) reference to 'self'.
  void Init(PyObject* self);
  // Get Python version of "this" to access virtual function implementation:
  //     ::clif::SafeAttr vfunc(self(), "v_func_name");
  PyObject* self() const;

  // Take/drop 'self' ownership.
  void HoldPyObj(PyObject* self);
  void DropPyObj();

 private:
  PyObject* PoisonPill() const;

  // A weak reference to 'self' for C++ callers into Python-holded instance.
  // Initialized by Init(py) call after the ctor (postcall).
  PyObject* self_ = nullptr;
  // Transfer python ownership here when 'self' released to an unique_ptr.
  PyObject* pyowner_ = nullptr;
};

extern "C" PyObject* pyclif_instance_dict_get(PyObject* self, void*);
extern "C" int pyclif_instance_dict_set(
    PyObject* self, PyObject* new_dict, void*);
extern "C" int pyclif_instance_dict_traverse(
    PyObject *self, visitproc visit, void *arg);
extern "C" int pyclif_instance_dict_clear(PyObject *self);
void pyclif_instance_dict_enable(PyTypeObject* ty, std::size_t dictoffset);
bool ensure_no_args_and_kw_args(const char* func, PyObject* args, PyObject* kw);

// https://docs.python.org/2/library/pickle.html#pickling-and-unpickling-extension-types
// https://docs.python.org/3/library/pickle.html#object.__reduce_ex__
PyObject* ReduceExImpl(PyObject* self, PyObject* args, PyObject* kw);

bool PyObjectTypeIsConvertibleToStdVector(PyObject* obj);
bool PyObjectTypeIsConvertibleToStdSet(PyObject* obj);
bool PyObjectTypeIsConvertibleToStdMap(PyObject* obj);

}  // namespace clif

#endif  // CLIF_PYTHON_RUNTIME_H_
