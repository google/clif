/*
 * Copyright 2023 Google LLC
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
#ifndef CLIF_TESTING_ALT_BYTES_H_
#define CLIF_TESTING_ALT_BYTES_H_

#include <Python.h>

#include <string>

#include "clif/python/postconv.h"
#include "clif/python/types.h"

namespace clif_testing_alt_bytes {

struct AltBytes {
  std::string data;
};

// CLIF use2 `clif_testing_alt_bytes::AltBytes` as bytes

inline bool Clif_PyObjAs(PyObject* obj, AltBytes* alt_bytes) {
  char* buffer;
  Py_ssize_t length;
  if (PyBytes_AsStringAndSize(obj, &buffer, &length) == -1) {
    return false;
  }
  *alt_bytes = AltBytes{std::string(buffer, length)};
  return true;
}

inline PyObject* Clif_PyObjFrom(const AltBytes& alt_bytes,
                                const ::clif::py::PostConv&) {
  return PyBytes_FromStringAndSize(alt_bytes.data.data(),
                                   alt_bytes.data.size());
}

inline std::string PassAltBytes(const AltBytes& alt_bytes) {
  return "PassAltBytes:" + alt_bytes.data;
}

inline AltBytes ReturnAltBytes(const std::string& std_string) {
  return AltBytes{"ReturnAltBytes:" + std_string};
}

}  // namespace clif_testing_alt_bytes

#endif  // CLIF_TESTING_ALT_BYTES_H_
