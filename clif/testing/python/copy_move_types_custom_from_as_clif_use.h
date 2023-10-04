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

#ifndef CLIF_TESTING_PYTHON_COPY_MOVE_TYPES_CUSTOM_FROM_AS_CLIF_USE_H_
#define CLIF_TESTING_PYTHON_COPY_MOVE_TYPES_CUSTOM_FROM_AS_CLIF_USE_H_

#include <Python.h>

#include <memory>

#include "clif/python/postconv.h"
#include "clif/testing/copy_move_types_custom_from_as.h"
#include "clif/testing/py_capsule_helpers.h"

namespace clif_testing::copy_move_types_custom_from_as {

// clang-format off
// CLIF use `::clif_testing::copy_move_types_custom_from_as::FromCRAsPPCopyMoveType` as FromCRAsPPCopyMoveType NOLINT
// clang-format on

inline PyObject* Clif_PyObjFrom(const FromCRAsPPCopyMoveType& c_obj,
                                const ::clif::py::PostConv&) {
  return py_capsule_helpers::MakePyCapsuleWithPayloadPointer(
      std::make_unique<FromCRAsPPCopyMoveType>(c_obj));
}

inline bool Clif_PyObjAs(PyObject* py_obj, FromCRAsPPCopyMoveType** c_obj) {
  return py_capsule_helpers::GetPayloadPointerFromPyCapsule(py_obj, c_obj);
}

}  // namespace clif_testing::copy_move_types_custom_from_as

#endif  // CLIF_TESTING_PYTHON_COPY_MOVE_TYPES_CUSTOM_FROM_AS_CLIF_USE_H_
