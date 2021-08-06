// Copyright 2021 Google LLC
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

#ifndef THIRD_PARTY_CLIF_PYBIND11_RUNTIME_H_
#define THIRD_PARTY_CLIF_PYBIND11_RUNTIME_H_

#include "Python.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "third_party/pybind11_abseil/status_casters.h"
#include "third_party/pybind11_abseil/status_not_ok_exception.h"
#include "util/task/python/clif/status_pyexc.h"


inline pybind11::object ConvertPyObject(PyObject* ptr) {
  if (PyErr_Occurred() || ptr == nullptr) {
    throw pybind11::error_already_set();
  }
  return pybind11::reinterpret_borrow<pybind11::object>(ptr);
}

namespace pybind11 {
namespace google {

template <typename StatusType>
struct PyCLIFStatus {
  PyCLIFStatus() = default;
  PyCLIFStatus(StatusType status_in)
      : status(std::forward<StatusType>(status_in)) { }
  StatusType status;
};

template <typename StatusType, typename... Args>
std::function<PyCLIFStatus<StatusType>(Args...)> ToPyCLIFStatus(
    StatusType (*f)(Args...)) {
  return [f](Args&&... args) {
    return PyCLIFStatus<StatusType>(
        std::forward<StatusType>(f(std::forward<Args>(args)...)));
  };
}

template <typename StatusType, typename Class, typename... Args>
std::function<PyCLIFStatus<StatusType>(Class*, Args...)> ToPyCLIFStatus(
    StatusType (Class::*f)(Args...)) {
  return [f](Class* c, Args&&... args) {
    return PyCLIFStatus<StatusType>(
        std::forward<StatusType>((c->*f)(std::forward<Args>(args)...)));
  };
}

template <typename StatusType, typename Class, typename... Args>
std::function<PyCLIFStatus<StatusType>(Class*, Args...)> ToPyCLIFStatus(
    StatusType (Class::*f)(Args...) const) {
  return [f](Class* c, Args&&... args) {
    return PyCLIFStatus<StatusType>(
        std::forward<StatusType>((c->*f)(std::forward<Args>(args)...)));
  };
}

}  // namespace google

namespace detail {

template <typename StatusType>
struct type_caster<google::PyCLIFStatus<StatusType>> {
  static constexpr auto name = _<google::PyCLIFStatus<StatusType>>();

  // Convert C++->Python.
  static handle cast(const google::PyCLIFStatus<StatusType>& src,
                     return_value_policy policy, handle parent) {
    try {
      return make_caster<StatusType>::cast(src.status, policy, parent);
    } catch (const google::StatusNotOk& e) {
      // Convert google::StatusNotOk to util.task.python.error.StatusNotOk
      util_task_python_clif::ErrorFromStatus(src.status);
      throw pybind11::error_already_set();
    }
    return none().release();
  }
};

}  // namespace detail
}  // namespace pybind11

#endif  // THIRD_PARTY_CLIF_PYBIND11_RUNTIME_H_
