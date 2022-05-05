/*
 * Copyright 2022 Google LLC
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
#ifndef CLIF_PYTHON_STLTYPES_FWD_H_
#define CLIF_PYTHON_STLTYPES_FWD_H_

/*
From .../python-2.7.3-docs-html/c-api/intro.html#include-files:
Since Python may define some pre-processor definitions which affect the
standard headers on some systems, you must include Python.h before any standard
headers are included.
*/
#include <Python.h>

#include <array>
#include <deque>
#include <functional>
#include <iterator>
#include <list>
#include <map>
#include <memory>
#include <queue>
#include <set>
#include <stack>
#include <tuple>
#include <type_traits>
#include <typeinfo>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <variant>
#include <vector>

// Clang and gcc define __EXCEPTIONS when -fexceptions flag passed to them.
// (see https://gcc.gnu.org/onlinedocs/cpp/Common-Predefined-Macros.html and
// http://llvm.org/releases/3.6.0/tools/clang/docs/ReleaseNotes.html#the-exceptions-macro)
// NOLINT(whitespace/line_length)
#ifdef __EXCEPTIONS
#include <system_error>  // NOLINT(build/c++11)
#endif                   // __EXCEPTIONS

#include "absl/base/config.h"
#include "absl/types/optional.h"
#include "absl/types/variant.h"
#include "clif/python/postconv.h"
#include "clif/python/pyproto.h"
#include "clif/python/types.h"

namespace clif {

// Declare Clif_PyObjAs and Clif_PyObjFrom for all STL types here before they
// are needed, e.g. by clif::py::ListFromSizableCont or clif::py::IterToCont.

template <typename R, typename... T>
bool Clif_PyObjAs(PyObject* py, std::function<R(T...)>* c,
                  const py::PostConv& pc = {});

template <typename T>
bool Clif_PyObjAs(PyObject* py, std::unique_ptr<T>* c);

// std::pair
template <typename T, typename U>
PyObject* Clif_PyObjFrom(const std::pair<T, U>& c, const py::PostConv& pc);
template <typename T, typename U>
bool Clif_PyObjAs(PyObject* py, std::pair<T, U>* c);

// std::tuple
template <typename... T>
PyObject* Clif_PyObjFrom(const std::tuple<T...>& c, const py::PostConv& pc);
template <typename... T>
bool Clif_PyObjAs(PyObject* py, std::tuple<T...>* c);

// std::optional
#ifdef ABSL_HAVE_STD_OPTIONAL
template <typename T>
PyObject* Clif_PyObjFrom(const std::optional<T>& opt,
                         const ::clif::py::PostConv& pc);
template <typename T>
bool Clif_PyObjAs(PyObject* py, std::optional<T>* c);
#endif  // ABSL_HAVE_STD_OPTIONAL

// std::vector
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::vector<T, Args...>& c,
                         const py::PostConv& pc);
template <typename... Args>
PyObject* Clif_PyObjFrom(const std::vector<bool, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(std::vector<T, Args...>&& c, const py::PostConv& pc);
template <typename... Args>
PyObject* Clif_PyObjFrom(std::vector<bool, Args...>&& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>

// std::list
PyObject* Clif_PyObjFrom(const std::list<T, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(std::list<T, Args...>&& c, const py::PostConv& pc);
template <typename T, typename... Args>

// Queue types
PyObject* Clif_PyObjFrom(const std::queue<T, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(std::queue<T, Args...>&& c, const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::priority_queue<T, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(std::priority_queue<T, Args...>&& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::deque<T, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(std::deque<T, Args...>&& c, const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::stack<T, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(std::stack<T, Args...>&& c, const py::PostConv& pc);

// std::array
template <typename T, std::size_t N>
bool Clif_PyObjAs(PyObject* py, std::array<T, N>* c);
template <typename T, std::size_t N>
PyObject* Clif_PyObjFrom(const std::array<T, N>& c, const py::PostConv& pc);
template <typename T, std::size_t N>
PyObject* Clif_PyObjFrom(std::array<T, N>&& c, const py::PostConv& pc);

// Map types
template <typename T, typename U, typename... Args>
PyObject* Clif_PyObjFrom(const std::unordered_map<T, U, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename U, typename... Args>
PyObject* Clif_PyObjFrom(std::unordered_map<T, U, Args...>&& c,
                         const py::PostConv& pc);

template <typename T, typename U, typename... Args>
PyObject* Clif_PyObjFrom(const std::map<T, U, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename U, typename... Args>
PyObject* Clif_PyObjFrom(std::map<T, U, Args...>&& c, const py::PostConv& pc);

// Set types
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::unordered_set<T, Args...>& c,
                         const py::PostConv& pc);
template <typename T, typename... Args>
PyObject* Clif_PyObjFrom(const std::set<T, Args...>& c, const py::PostConv& pc);

#ifdef ABSL_HAVE_STD_VARIANT
inline PyObject* Clif_PyObjFrom(const ::std::monostate,
                                const ::clif::py::PostConv& conv);
inline bool Clif_PyObjAs(PyObject* py, ::std::monostate* v);
template <typename... U>
PyObject* Clif_PyObjFrom(const ::std::variant<U...>& v,
                         const ::clif::py::PostConv& conv);
template <typename... U>
bool Clif_PyObjAs(PyObject* obj, ::std::variant<U...>* v);
#endif  // ABSL_HAVE_STD_VARIANT

}  // namespace clif

#endif  // CLIF_PYTHON_STLTYPES_FWD_H_
