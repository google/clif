#ifndef THIRD_PARTY_CLIF_PYBIND11_STATUS_CASTERS_H_
#define THIRD_PARTY_CLIF_PYBIND11_STATUS_CASTERS_H_

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "third_party/pybind11_abseil/status_casters.h"
#include "third_party/pybind11_abseil/status_not_ok_exception.h"
#include "util/task/python/clif/status_pyexc.h"

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

template <>
struct type_caster<google::PyCLIFStatus<absl::Status>> {
  static constexpr auto name = _<google::PyCLIFStatus<absl::Status>>();

  // Convert C++->Python.
  static handle cast(const google::PyCLIFStatus<absl::Status>& src,
                     return_value_policy policy, handle parent) {
    try {
      return make_caster<absl::Status>::cast(src.status, policy, parent);
    } catch (const google::StatusNotOk& e) {
      // Convert google::StatusNotOk to util.task.python.error.StatusNotOk
      util_task_python_clif::ErrorFromStatus(src.status);
      throw pybind11::error_already_set();
    }
    return none().release();
  }
};

template <typename PayloadType>
struct type_caster<google::PyCLIFStatus<absl::StatusOr<PayloadType>>> {
  static constexpr auto name =
      _<google::PyCLIFStatus<absl::StatusOr<PayloadType>>>();

  // Convert C++->Python.
  static handle cast(
      const google::PyCLIFStatus<absl::StatusOr<PayloadType>>& src,
      return_value_policy policy, handle parent) {
    try {
      return make_caster<absl::StatusOr<PayloadType>>::cast(
          src.status, policy, parent);
    } catch (const google::StatusNotOk& e) {
      // Convert google::StatusNotOk to util.task.python.error.StatusNotOk
      util_task_python_clif::ErrorFromStatus(src.status.status());
      throw pybind11::error_already_set();
    }
    return none().release();
  }
};

}  // namespace detail
}  // namespace pybind11

#endif  // THIRD_PARTY_CLIF_PYBIND11_STATUS_CASTERS_H_
