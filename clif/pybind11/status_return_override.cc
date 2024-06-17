#include "clif/pybind11/status_return_override.h"

#include "absl/log/check.h"
#include "absl/status/status.h"
#include "third_party/pybind11/include/pybind11/pybind11.h"
#include "third_party/pybind11_abseil/compat/status_from_py_exc.h"

namespace clif_pybind11 {

absl::Status StatusFromErrorAlreadySet(pybind11::error_already_set& e) {
  CHECK(PyGILState_Check());
  e.restore();
  return pybind11_abseil::compat::StatusFromPyExcGivenErrOccurred();
}

}  // namespace clif_pybind11
