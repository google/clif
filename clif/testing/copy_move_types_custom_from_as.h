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

#ifndef CLIF_TESTING_COPY_MOVE_TYPES_CUSTOM_FROM_AS_H_
#define CLIF_TESTING_COPY_MOVE_TYPES_CUSTOM_FROM_AS_H_

#include <memory>
#include <optional>
#include <string>

#include "clif/testing/copy_move_types_library.h"

namespace clif_testing::copy_move_types_custom_from_as {

using copy_move_types_library::CopyMoveType;

// Need to hide inheritance to get the correct `Clif_PyObjAs()`.
// For clif_type_casters that use `Type` to hold the value:
// http://google3/clif/pybind11/clif_type_casters.h;l=177;rcl=570854707
class FromCRAsPCopyMoveType : private CopyMoveType {
 public:
  FromCRAsPCopyMoveType() = default;
  explicit FromCRAsPCopyMoveType(const CopyMoveType& obj)
      : CopyMoveType{obj} {}
  using CopyMoveType::GetTrace;
};

inline FromCRAsPCopyMoveType MakeFromCRAsPCopyMoveType(
    const CopyMoveType& class_obj) {
  return FromCRAsPCopyMoveType{class_obj};
}

inline std::string GetTraceFromCRAsPCopyMoveType(
    const FromCRAsPCopyMoveType& cfa_obj) {
  return cfa_obj.GetTrace();
}

// For clif_type_casters that use `std::optional<Type>` to hold the value:
// http://google3/clif/pybind11/clif_type_casters.h;l=193;rcl=570854707
class FromCRAsOpCopyMoveType : private CopyMoveType {
 public:
  FromCRAsOpCopyMoveType() = default;
  explicit FromCRAsOpCopyMoveType(const CopyMoveType& obj)
      : CopyMoveType{obj} {}
  using CopyMoveType::GetTrace;
};

inline FromCRAsOpCopyMoveType MakeFromCRAsOpCopyMoveType(
    const CopyMoveType& class_obj) {
  return FromCRAsOpCopyMoveType{class_obj};
}

inline std::string GetTraceFromCRAsOpCopyMoveType(
    std::optional<FromCRAsOpCopyMoveType> cfa_obj) {
  return cfa_obj.value().GetTrace();
}

// For clif_type_casters that use `Type*` to hold the value:
// http://google3/clif/pybind11/clif_type_casters.h;l=219;rcl=570854707
class FromCRAsPPCopyMoveType : private CopyMoveType {
 public:
  explicit FromCRAsPPCopyMoveType(const CopyMoveType& obj)
      : CopyMoveType{obj} {}
  using CopyMoveType::GetTrace;
};

inline FromCRAsPPCopyMoveType MakeFromCRAsPPCopyMoveType(
    const CopyMoveType& class_obj) {
  return FromCRAsPPCopyMoveType{class_obj};
}

inline std::string GetTraceFromCRAsPPCopyMoveType(
    const FromCRAsPPCopyMoveType& cfa_obj) {
  return cfa_obj.GetTrace();
}

// For clif_type_casters that use `std::unique_ptr<Type>` to hold the value:
// http://google3/clif/pybind11/clif_type_casters.h;l=247;rcl=570854707
class FromCRAsUpCopyMoveType : private CopyMoveType {
 public:
  FromCRAsUpCopyMoveType() = default;
  explicit FromCRAsUpCopyMoveType(const CopyMoveType& obj)
      : CopyMoveType{obj} {}
  using CopyMoveType::GetTrace;
};

inline FromCRAsUpCopyMoveType MakeFromCRAsUpCopyMoveType(
    const CopyMoveType& class_obj) {
  return FromCRAsUpCopyMoveType{class_obj};
}

inline std::string GetTraceFromCRAsUpCopyMoveType(
    std::unique_ptr<FromCRAsUpCopyMoveType> cfa_obj) {
  return cfa_obj->GetTrace();
}

// For clif_type_casters that use `std::shared_ptr<Type>` to hold the value:
// http://google3/clif/pybind11/clif_type_casters.h;l=285;rcl=570854707
class FromCRAsSpCopyMoveType : private CopyMoveType {
 public:
  FromCRAsSpCopyMoveType() = default;
  explicit FromCRAsSpCopyMoveType(const CopyMoveType& obj)
      : CopyMoveType{obj} {}
  using CopyMoveType::GetTrace;
};

inline FromCRAsSpCopyMoveType MakeFromCRAsSpCopyMoveType(
    const CopyMoveType& class_obj) {
  return FromCRAsSpCopyMoveType{class_obj};
}

inline std::string GetTraceFromCRAsSpCopyMoveType(
    FromCRAsSpCopyMoveType* cfa_obj) {
  return cfa_obj->GetTrace();
}

}  // namespace clif_testing::copy_move_types_custom_from_as

#endif  // CLIF_TESTING_COPY_MOVE_TYPES_CUSTOM_FROM_AS_H_
