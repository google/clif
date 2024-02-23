// Copyright 2024 Google LLC
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

#ifndef CLIF_PYBIND11_PYCLIF_PYBIND11_MODULE_MACRO_H_
#define CLIF_PYBIND11_PYCLIF_PYBIND11_MODULE_MACRO_H_

#include "third_party/pybind11/include/pybind11/pybind11.h"
#include "third_party/pybind11_protobuf/native_proto_caster.h"

#define PYCLIF_PYBIND11_MODULE(CLIF_SOURCE_FILENAME, PYINIT_NAME, MODULE_NAME) \
  extern "C" PyObject* PYINIT_NAME() {                                         \
    PYBIND11_CHECK_PYTHON_VERSION                                              \
    PYBIND11_ENSURE_INTERNALS_READY                                            \
    static pybind11::module_::module_def this_module_def;                      \
    auto m = pybind11::module_::create_extension_module(MODULE_NAME, nullptr,  \
                                                        &this_module_def);     \
    try {                                                                      \
      m.attr("__pyclif_codegen_mode__") = "pybind11";                          \
      m.doc() = "CLIF-generated module for " CLIF_SOURCE_FILENAME;             \
      pybind11_protobuf::check_unknown_fields::                                \
          ExtensionsWithUnknownFieldsPolicy::                                  \
              WeakEnableFallbackToSerializeParse();                            \
      pybind11_protobuf::ImportNativeProtoCasters();                           \
      PyclifPybind11ModuleInit(m);                                             \
      return m.ptr();                                                          \
    }                                                                          \
    PYBIND11_CATCH_INIT_EXCEPTIONS                                             \
  }

#endif  // CLIF_PYBIND11_PYCLIF_PYBIND11_MODULE_MACRO_H_
