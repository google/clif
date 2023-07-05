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
#ifndef CLIF_PYTHON_TYPES_H_
#define CLIF_PYTHON_TYPES_H_

/* "Standard" types known to CLIF. */

/*
From https://docs.python.org/3/c-api/intro.html#include-files:
Since Python may define some pre-processor definitions which affect the
standard headers on some systems, you must include Python.h before any standard
headers are included.
*/
#include <Python.h>

#include <algorithm>
#include <array>
#include <complex>
#include <deque>
#include <forward_list>
#include <functional>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>


#include "glog/logging.h"
#include "absl/base/config.h"
#include "absl/numeric/int128.h"
#include "absl/strings/cord.h"
#include "absl/strings/string_view.h"
#include "absl/types/optional.h"
#include "absl/types/variant.h"

// std::variant support is implemented in stltypes.h which our generated code
// #include's directly.  But that file is not parsed for "CLIF" use statements.
// CLIF use `::std::variant` as OneOf
// CLIF use `::std::monostate` as Monostate

#include "clif/python/postconv.h"
#include "clif/python/pyobject_ptr_conv.h"
// Protobuf type declared here because subincludes are not scanned for types.
// CLIF use `::proto2::Message` as proto2_Message
#include "clif/python/pyproto.h"
#include "clif/python/runtime.h"

namespace clif {
using std::swap;

//
// To Python conversions.
//

// CLIF use `PyObject*` as object

// int (long)
// pyport.h should define Py_ssize_t as either int or long
static_assert((std::is_same<Py_ssize_t, int>::value ||
               std::is_same<Py_ssize_t, long>::value),  // NOLINT runtime/int
              "The world is strange");
// CLIF use `int` as int
inline PyObject* Clif_PyObjFrom(int c, const py::PostConv& pc) {
  return pc.Apply(PyLong_FromLong(c));
}
// CLIF use `unsigned int` as uint
inline PyObject* Clif_PyObjFrom(unsigned int c, const py::PostConv& pc) {
  return pc.Apply(PyLong_FromSize_t(c));
}
#ifdef uint32_t
// CLIF use `uint32` as uint32
inline PyObject* Clif_PyObjFrom(uint32_t c, const py::PostConv& pc) {
  return pc.Apply(PyLong_FromSize_t(c));
}
#endif
// CLIF use `long` as long
inline PyObject* Clif_PyObjFrom(long c,  // NOLINT runtime/int
                                const py::PostConv& pc) {
  return pc.Apply(PyLong_FromLong(c));
}
// CLIF use `ulong` as ulong
inline PyObject* Clif_PyObjFrom(unsigned long c,  // NOLINT runtime/int
                                const py::PostConv& pc) {
  return pc.Apply(PyLong_FromSize_t(c));
}
// CLIF use `int64` as int64
#ifdef HAVE_LONG_LONG
inline PyObject* Clif_PyObjFrom(long long c,  // NOLINT runtime/int
                                const py::PostConv& pc) {
  return pc.Apply(PyLong_FromLongLong(c));
}
// CLIF use `uint64` as uint64
inline PyObject* Clif_PyObjFrom(unsigned long long c,  // NOLINT runtime/int
                                const py::PostConv& pc) {
  return pc.Apply(PyLong_FromUnsignedLongLong(c));
}

// CLIF use `absl::int128` as int128
inline PyObject* Clif_PyObjFrom(absl::int128 c, const py::PostConv& pc) {
  auto hi = PyNumber_Lshift(PyLong_FromLongLong(absl::Int128High64(c)),
                            PyLong_FromLong(64));
  auto lo = PyLong_FromUnsignedLongLong(absl::Int128Low64(c));
  return pc.Apply(PyNumber_Add(hi, lo));
}

// CLIF use `absl::uint128` as uint128
inline PyObject* Clif_PyObjFrom(absl::uint128 c, const py::PostConv& pc) {
  auto hi = PyNumber_Lshift(PyLong_FromUnsignedLongLong(absl::Uint128High64(c)),
                            PyLong_FromLong(64));
  auto lo = PyLong_FromUnsignedLongLong(absl::Uint128Low64(c));
  return pc.Apply(PyNumber_Add(hi, lo));
}
#endif
// CLIF use `unsigned char` as uint8
inline PyObject* Clif_PyObjFrom(unsigned char c, const py::PostConv& pc) {
  return pc.Apply(PyLong_FromLong(c));
}

// float (double)
// CLIF use `float` as float
// CLIF use `double` as float
inline PyObject* Clif_PyObjFrom(double c, const py::PostConv& pc) {
  return pc.Apply(PyFloat_FromDouble(c));
}

// CLIF use `std::complex<double>` as complex.
// CLIF use `std::complex<float>` as complex.
inline PyObject* Clif_PyObjFrom(std::complex<double> c,
                                const py::PostConv& pc) {
  return pc.Apply(PyComplex_FromDoubles(c.real(), c.imag()));
}

// CLIF use `bool` as bool
#ifdef CLIF_PY_OBJ_FROM_BOOL_ALLOW_UNSAFE_IMPLICIT_CONVERSIONS
inline PyObject* Clif_PyObjFrom(bool c, const py::PostConv& pc) {
#else
template <typename T>
typename std::enable_if<std::is_same<T, bool>::value, PyObject*>::type  //
    inline Clif_PyObjFrom(T c, const py::PostConv& pc) {
#endif
  return pc.Apply(PyBool_FromLong(c));
}

PyObject* Clif_PyObjFrom(std::string_view, const py::PostConv&);
// CLIF use `::std::string` as bytes

typedef const char* char_ptr;  // A distinct type for constexpr CONST string.
inline PyObject* Clif_PyObjFrom(const char_ptr c, const py::PostConv& unused) {
  // Always use native str, ignore postconversion.
  return PyUnicode_FromString(c);
}

// CLIF use `::std::optional` as NoneOr
#ifdef ABSL_HAVE_STD_OPTIONAL
template <typename T>
PyObject* Clif_PyObjFrom(const std::optional<T>& opt, const py::PostConv&);
template <typename T>
bool Clif_PyObjAs(PyObject*, std::optional<T>*);
#endif

//
// From Python conversions.
//

// int (long)
bool Clif_PyObjAs(PyObject*, signed char*);
bool Clif_PyObjAs(PyObject*, unsigned char*);
bool Clif_PyObjAs(PyObject*, unsigned short*);  // NOLINT runtime/int
bool Clif_PyObjAs(PyObject*, unsigned int*);
bool Clif_PyObjAs(PyObject*, unsigned long*);  // NOLINT runtime/int
#ifdef HAVE_LONG_LONG
bool Clif_PyObjAs(PyObject*, unsigned long long*);  // NOLINT runtime/int
bool Clif_PyObjAs(PyObject*, long long*);           // NOLINT runtime/int
bool Clif_PyObjAs(PyObject*, absl::int128*);        // NOLINT runtime/int
bool Clif_PyObjAs(PyObject*, absl::uint128*);       // NOLINT runtime/int
#endif
bool Clif_PyObjAs(PyObject*, short*);  // NOLINT runtime/int
bool Clif_PyObjAs(PyObject*, int*);
bool Clif_PyObjAs(PyObject*, long*);  // NOLINT runtime/int // Py_ssize_t on x64

// float (double)
bool Clif_PyObjAs(PyObject*, double*);
bool Clif_PyObjAs(PyObject*, float*);

// complex
bool Clif_PyObjAs(PyObject*, std::complex<double>*);
bool Clif_PyObjAs(PyObject*, std::complex<float>*);

// bool
bool Clif_PyObjAs(PyObject*, bool*);

// bytes
bool Clif_PyObjAs(PyObject*, std::string*);
bool Clif_PyObjAs(PyObject* py, std::shared_ptr<std::string>* c);
bool Clif_PyObjAs(PyObject*, std::string_view*);

PyObject* UnicodeFromBytes(PyObject*);

// Reusing non-const T* conversion for const T*.
template <typename T>
bool Clif_PyObjAs(PyObject* py, const T** c) {
  T* nonconst_ptr = nullptr;
  bool ok = Clif_PyObjAs(py, &nonconst_ptr);
  *c = nonconst_ptr;
  return ok;
}

//
// Containers
//
// CLIF use `std::array` as list
// CLIF use `std::list` as list
// CLIF use `std::queue` as list
// CLIF use `std::priority_queue` as list
// CLIF use `std::stack` as list
// CLIF use `std::deque` as list
// CLIF use `std::vector` as list

template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::vector<T, Args...>& c, const py::PostConv&);
template <typename... Args>
PyObject* Clif_PyObjFrom(const std::vector<bool, Args...>& c,
                         const py::PostConv&);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(std::vector<T, Args...>&& c, const py::PostConv&);
template <typename... Args>
PyObject* Clif_PyObjFrom(std::vector<bool, Args...>&& c, const py::PostConv&);

template <typename T, typename... Args>
bool Clif_PyObjAs(PyObject* py, std::vector<T, Args...>* c);

// CLIF use `std::pair` as tuple
template <typename T, typename U>
PyObject* Clif_PyObjFrom(const std::pair<T, U>& c, const py::PostConv&);
template <typename T, typename U>
bool Clif_PyObjAs(PyObject* py, std::pair<T, U>* c);
template <typename... T>
PyObject* Clif_PyObjFrom(const std::tuple<T...>& c, const py::PostConv&);
template <typename... T>
bool Clif_PyObjAs(PyObject* py, std::tuple<T...>* c);

// CLIF use `std::map` as dict
// CLIF use `std::unordered_map` as dict
template <typename T, typename U, typename... Args>
PyObject* Clif_PyObjFrom(const std::unordered_map<T, U, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename U, typename... Args>
bool Clif_PyObjAs(PyObject* py, std::unordered_map<T, U, Args...>* c);

template <typename T, typename U, typename... Args>
PyObject* Clif_PyObjFrom(const std::map<T, U, Args...>& c, const py::PostConv&);
template <typename T, typename U, typename... Args>
bool Clif_PyObjAs(PyObject* py, std::map<T, U, Args...>* c);

// CLIF use `std::set` as set
// CLIF use `std::unordered_set` as set
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::unordered_set<T, Args...>& c,
                         const py::PostConv&);
template <typename T, typename... Args>
bool Clif_PyObjAs(PyObject* py, std::unordered_set<T, Args...>* c);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::set<T, Args...>& c, const py::PostConv&);
template <typename T, typename... Args>
bool Clif_PyObjAs(PyObject* py, std::set<T, Args...>* c);

// ---------------------------------------------------------------------
// Fill in extra overloads for copyable types.

// Just is_copy_assignable<T> is not enough here as From(T*) will engage in
// T*&& resolution instead of generated (for capsule) const T*, so implement a
// direct check if From(T) is available.
template <typename T,
          typename = decltype(Clif_PyObjFrom(std::declval<T>(), {}))>
inline PyObject* Clif_PyObjFrom(T* c, const py::PostConv& pc) {
  if (c) return Clif_PyObjFrom(*c, pc);
  Py_RETURN_NONE;
}
template <typename T>
typename std::enable_if<std::is_copy_assignable<T>::value, PyObject*>::type  //
    inline Clif_PyObjFrom(const std::unique_ptr<T>& c, const py::PostConv& pc) {
  if (c) return Clif_PyObjFrom(*c, pc);
  Py_RETURN_NONE;
}

namespace callback {

// This class is used to convert return values from callbacks and virtual
// functions implemented in Python to C++. It deals with converting Python
// objects returned under normal conditions, as well as error conditions
// expressed by raising exceptions in Python, into appropriate C++ return
// values of type R.
//
// A generic version of this class is defined in
// clif/python/stltypes.h.
//
// See util/task/python/clif.h for examples of specializations of this class
// for Status and StatusOr values (ie., when R = Status or R = StatusOr<T>).
template <typename R>
class ReturnValue;

}  // namespace callback
}  // namespace clif

#endif  // CLIF_PYTHON_TYPES_H_
