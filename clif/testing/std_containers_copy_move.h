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
#ifndef CLIF_TESTING_STD_CONTAINERS_COPY_MOVE_H_
#define CLIF_TESTING_STD_CONTAINERS_COPY_MOVE_H_

#include <array>
#include <string>
#include <vector>

#include "clif/testing/copy_move_types_custom_from_as.h"
#include "clif/testing/copy_move_types_library.h"

namespace clif_testing::std_containers_copy_move {

using copy_move_types_library::CopyMoveType;
using copy_move_types_library::CopyOnlyType;
using copy_move_types_library::MoveOnlyType;
using copy_move_types_library::StayPutType;

using copy_move_types_custom_from_as::FromCRAsPPCopyMoveType;

template <typename SeqType>
std::string PassSeqType(SeqType& vec) {
  std::string traces;
  for (const auto& it : vec) {
    traces += it.GetTrace() + "@";
  }
  return traces;
}

template <typename SeqType>
std::string PassSeqTypeItemPtr(SeqType& vec) {
  std::string traces;
  for (const auto& it : vec) {
    traces += it->GetTrace() + "@";
  }
  return traces;
}

//
// std::vector
//

inline std::string PassStdVectorCopyMoveType(
    const std::vector<CopyMoveType>& seq) {
  return PassSeqType(seq);
}
inline std::string PassStdVectorCopyOnlyType(
    const std::vector<CopyOnlyType>& seq) {
  return PassSeqType(seq);
}
inline std::string PassStdVectorMoveOnlyType(
    const std::vector<MoveOnlyType>& seq) {
  return PassSeqType(seq);
}
inline std::string PassStdVectorStayPutTypePtr(
    const std::vector<StayPutType*>& seq) {
  return PassSeqTypeItemPtr(seq);
}

inline std::string PassStdVectorFromCRAsPPCopyMoveType(
    const std::vector<FromCRAsPPCopyMoveType>& seq) {
  return PassSeqType(seq);
}

//
// std::array
//

inline std::string PassStdArray1CopyMoveType(
    const std::array<CopyMoveType, 1>& seq) {
  return PassSeqType(seq);
}
inline std::string PassStdArray1CopyOnlyType(
    const std::array<CopyOnlyType, 1>& seq) {
  return PassSeqType(seq);
}
inline std::string PassStdArray1MoveOnlyType(
    const std::array<MoveOnlyType, 1>& seq) {
  return PassSeqType(seq);
}
inline std::string PassStdArray1StayPutTypePtr(
    const std::array<StayPutType*, 1>& seq) {
  return PassSeqTypeItemPtr(seq);
}

}  // namespace clif_testing::std_containers_copy_move

#endif  // CLIF_TESTING_STD_CONTAINERS_COPY_MOVE_H_
