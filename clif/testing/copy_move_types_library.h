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

#ifndef CLIF_TESTING_COPY_MOVE_TYPES_LIBRARY_H_
#define CLIF_TESTING_COPY_MOVE_TYPES_LIBRARY_H_

#include <string>
#include <string_view>

namespace clif_testing::copy_move_types_library {

// Intentionally not using inheritance, to ensure each type is completely
// self-contained and does not trigger any inheritance-related functionality.

class CopyMoveType {
 private:
  std::string trace_;

 public:
  const std::string &GetTrace() const { return trace_; }

  explicit CopyMoveType(std::string_view trace = "DefaultCtor")
      : trace_(trace) {}

  CopyMoveType(const CopyMoveType &other) { trace_ = other.trace_ + "_CpCtor"; }

  CopyMoveType &operator=(const CopyMoveType &rhs) {
    trace_ = rhs.trace_ + "_CpLhs";
    return *this;
  }

  CopyMoveType(CopyMoveType &&other) {
    trace_ = other.trace_ + "_MvCtorTo";
    other.trace_ += "_MvCtorFrom";
  }

  CopyMoveType &operator=(CopyMoveType &&rhs) {
    trace_ = rhs.trace_ + "_MvLhs";
    rhs.trace_ += "_MvRhs";
    return *this;
  }
};

class CopyOnlyType {
 private:
  std::string trace_;

 public:
  const std::string &GetTrace() const { return trace_; }

  explicit CopyOnlyType(std::string_view trace = "DefaultCtor")
      : trace_(trace) {}

  CopyOnlyType(const CopyOnlyType &other) { trace_ = other.trace_ + "_CpCtor"; }

  CopyOnlyType &operator=(const CopyOnlyType &rhs) {
    trace_ = rhs.trace_ + "_CpLhs";
    return *this;
  }

  CopyOnlyType(CopyOnlyType &&) = delete;

  CopyOnlyType &operator=(CopyOnlyType &&) = delete;
};

class MoveOnlyType {
 private:
  std::string trace_;

 public:
  const std::string &GetTrace() const { return trace_; }

  explicit MoveOnlyType(std::string_view trace = "DefaultCtor")
      : trace_(trace) {}

  MoveOnlyType(const MoveOnlyType &) = delete;

  MoveOnlyType &operator=(const MoveOnlyType &) = delete;

  MoveOnlyType(MoveOnlyType &&other) {
    trace_ = other.trace_ + "_MvCtorTo";
    other.trace_ += "_MvCtorFrom";
  }

  MoveOnlyType &operator=(MoveOnlyType &&rhs) {
    trace_ = rhs.trace_ + "_MvLhs";
    rhs.trace_ += "_MvRhs";
    return *this;
  }
};

class StayPutType {
 private:
  std::string trace_;

 public:
  const std::string &GetTrace() const { return trace_; }

  explicit StayPutType(std::string_view trace = "DefaultCtor")
      : trace_(trace) {}

  StayPutType(const StayPutType &) = delete;

  StayPutType &operator=(const StayPutType &) = delete;

  StayPutType(StayPutType &&) = delete;

  StayPutType &operator=(StayPutType &&) = delete;
};

}  // namespace clif_testing::copy_move_types_library

#endif  // CLIF_TESTING_COPY_MOVE_TYPES_LIBRARY_H_
