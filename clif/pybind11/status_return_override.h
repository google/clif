#ifndef CLIF_PYBIND11_STATUS_RETURN_OVERRIDE_H_
#define CLIF_PYBIND11_STATUS_RETURN_OVERRIDE_H_

// pybind11 includes have to be at the very top, even before Python.h
#include "third_party/pybind11/include/pybind11/detail/common.h"
#include "third_party/pybind11/include/pybind11/gil.h"
#include "third_party/pybind11/include/pybind11/pybind11.h"  // NOLINT(build/include_order)

// Must be after pybind11 include.
#include <string>  // NOLINT(build/include_order)

#include "absl/status/status.h"
#include "absl/status/statusor.h"
#include "third_party/pybind11/include/pybind11/pytypes.h"

namespace clif_pybind11 {

absl::Status StatusFromErrorAlreadySet(pybind11::error_already_set& e);

template<typename U>
pybind11::function GetOverload(
    const U* this_ptr, const std::string& function_name) {
  pybind11::gil_scoped_acquire gil;
  return pybind11::get_overload(static_cast<const U *>(this_ptr),
                                function_name.c_str());
}

template <typename U, typename... Ts>
absl::Status CatchErrorAlreadySetAndReturnStatus(
    const U* this_ptr, const std::string& function_name,
    const pybind11::return_value_policy_pack rvpp, Ts... args) {
  try {
    pybind11::function overload = GetOverload(this_ptr, function_name);
    if (!overload) {
      return absl::Status(absl::StatusCode::kUnimplemented,
                          "No Python overload is defined for " + function_name +
                          ".");
    }
    overload.call_with_policies(rvpp, args...); /* Ignoring return value. */
    return absl::OkStatus();
  } catch (pybind11::error_already_set &e) {
    return StatusFromErrorAlreadySet(e);
  }
}

template <typename StatusOrPayload, typename U, typename... Ts>
StatusOrPayload CatchErrorAlreadySetAndReturnStatusOr(
    const U* this_ptr, const std::string& function_name,
    const pybind11::return_value_policy_pack rvpp, Ts... args) {
  try {
    pybind11::function overload = GetOverload(this_ptr, function_name);
    if (!overload) {
      return absl::Status(absl::StatusCode::kUnimplemented,
                          "No Python overload is defined for " + function_name +
                          ".");
    }
    auto o = overload.call_with_policies(rvpp, args...);
    return o.template cast<StatusOrPayload>();
  } catch (pybind11::error_already_set &e) {
    return StatusFromErrorAlreadySet(e);
  }
}

}  // namespace clif_pybind11

// Similar with macro `PYBIND11_OVERLOAD_PURE` defined in pybind11/pybind11.h,
// but catches all exceptions derived from pybind11::error_already_set and
// converts the exception to a StatusNotOk return.
#define PYBIND11_OVERRIDE_PURE_STATUS_RETURN(cname, name, fn, rvpp, ...) \
  return ::clif_pybind11::CatchErrorAlreadySetAndReturnStatus(           \
      this, name, rvpp, ##__VA_ARGS__);

#define PYBIND11_OVERRIDE_PURE_STATUSOR_RETURN(statusor_payload_type, cname, \
                                               name, fn, rvpp, ...)          \
  return ::clif_pybind11::CatchErrorAlreadySetAndReturnStatusOr<             \
      statusor_payload_type>(this, name, rvpp, ##__VA_ARGS__);

#define PYBIND11_OVERRIDE_STATUS_RETURN(cname, name, fn, rvpp, ...)       \
  pybind11::function overload = ::clif_pybind11::GetOverload(this, name); \
  if (overload) {                                                         \
    return ::clif_pybind11::CatchErrorAlreadySetAndReturnStatus(          \
        this, name, rvpp, ##__VA_ARGS__);                                 \
  } else {                                                                \
    return cname::fn(__VA_ARGS__);                                        \
  }

#define PYBIND11_OVERRIDE_STATUSOR_RETURN(statusor_payload_type, cname, name, \
                                          fn, rvpp, ...)                      \
  pybind11::function overload = ::clif_pybind11::GetOverload(this, name);     \
  if (overload) {                                                             \
    return ::clif_pybind11::CatchErrorAlreadySetAndReturnStatusOr<            \
        statusor_payload_type>(this, name, rvpp, ##__VA_ARGS__);              \
  } else {                                                                    \
    return cname::fn(__VA_ARGS__);                                            \
  }

#endif  // CLIF_PYBIND11_STATUS_RETURN_OVERRIDE_H_
