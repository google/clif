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

#include <string>

#include "clif/testing/copy_move_types_library.h"

namespace clif_testing::copy_move_types_custom_from_as {

using copy_move_types_library::CopyMoveType;

// Need to hide inheritance to get the correct `Clif_PyObjAs()`.
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

}  // namespace clif_testing::copy_move_types_custom_from_as

#endif  // CLIF_TESTING_COPY_MOVE_TYPES_CUSTOM_FROM_AS_H_
