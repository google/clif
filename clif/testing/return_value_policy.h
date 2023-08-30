/*
 * Copyright 2021 Google LLC
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

#ifndef CLIF_TESTING_RETURN_VALUE_POLICY_H_
#define CLIF_TESTING_RETURN_VALUE_POLICY_H_

#include <memory>
#include <string>
#include <string_view>

namespace clif_testing {

struct Obj {
  std::string mtxt;
  Obj() : mtxt("DefaultConstructor") {}
  Obj(std::string_view mtxt_) : mtxt(mtxt_) {}
  Obj(const Obj &other) { mtxt = other.mtxt + "_CpCtor"; }
  Obj(Obj &&other) { mtxt = other.mtxt + "_MvCtor"; }

  Obj& operator=(const Obj &other) {
    mtxt = other.mtxt + "_CpCtor";
    return *this;
  }
  Obj& operator=(Obj &&other) {
    mtxt = other.mtxt + "_MvCtor";
    return *this;
  }
};

inline std::string return_string() {
  return "return_string";
}

inline Obj return_value() {
  return Obj{"return_value"};
}

inline Obj& return_reference() {
  static Obj obj;
  obj.mtxt = "return_reference";
  return obj;
}

inline const Obj& return_const_reference() {
  static Obj obj;
  obj.mtxt = "return_const_reference";
  return obj;
}

inline Obj* return_pointer() {
  static Obj obj;
  obj.mtxt = "return_pointer";
  return &obj;
}

inline const Obj* return_const_pointer() {
  static Obj obj;
  obj.mtxt = "return_const_pointer";
  return &obj;
}

inline std::shared_ptr<Obj> return_shared_pointer() {
  return std::shared_ptr<Obj>(new Obj{"return_shared_pointer"});
}

inline std::unique_ptr<Obj> return_unique_pointer() {
  return std::unique_ptr<Obj>(new Obj{"return_unique_pointer"});
}

struct NoCopy {
  std::string mtxt;
  NoCopy() : mtxt("DefaultConstructor") {}
  NoCopy(std::string_view mtxt_) : mtxt(mtxt_) {}
  NoCopy(const NoCopy&) = delete;
  NoCopy(NoCopy&& other) { mtxt = other.mtxt + "_MvCtor"; }

  NoCopy& operator=(const NoCopy &) = delete;
  NoCopy& operator=(NoCopy&& other) {
    mtxt = other.mtxt + "_MvCtor";
    return *this;
  }
};

inline NoCopy return_value_nocopy() {
  return NoCopy{"return_value_nocopy"};
}

inline NoCopy& return_reference_nocopy() {
  static NoCopy obj;
  obj.mtxt = "return_reference_nocopy";
  return obj;
}

inline NoCopy* return_pointer_nocopy() {
  static NoCopy obj;
  obj.mtxt = "return_pointer_nocopy";
  return &obj;
}

inline std::shared_ptr<NoCopy> return_shared_pointer_nocopy() {
  return std::shared_ptr<NoCopy>(new NoCopy{"return_shared_pointer_nocopy"});
}

inline std::unique_ptr<NoCopy> return_unique_pointer_nocopy() {
  return std::unique_ptr<NoCopy>(new NoCopy{"return_unique_pointer_nocopy"});
}

struct NoMove {
  std::string mtxt;
  NoMove() : mtxt("DefaultConstructor") {}
  NoMove(std::string_view mtxt_) : mtxt(mtxt_) {}
  NoMove(const NoMove &other) { mtxt = other.mtxt + "_CpCtor"; }

  NoMove& operator=(const NoMove &other) {
    mtxt = other.mtxt + "_CpCtor";
    return *this;
  }
};

inline NoMove return_value_nomove() {
  return NoMove{"return_value_nomove"};
}

inline NoMove& return_reference_nomove() {
  static NoMove obj;
  obj.mtxt = "return_reference_nomove";
  return obj;
}

inline NoMove* return_pointer_nomove() {
  static NoMove obj;
  obj.mtxt = "return_pointer_nomove";
  return &obj;
}

inline const NoMove& return_const_reference_nomove() {
  static NoMove obj;
  obj.mtxt = "return_const_reference_nomove";
  return obj;
}

inline const NoMove* return_const_pointer_nomove() {
  static NoMove obj;
  obj.mtxt = "return_const_pointer_nomove";
  return &obj;
}

inline std::shared_ptr<NoMove> return_shared_pointer_nomove() {
  return std::shared_ptr<NoMove>(new NoMove{"return_shared_pointer_nomove"});
}

inline std::unique_ptr<NoMove> return_unique_pointer_nomove() {
  return std::unique_ptr<NoMove>(new NoMove{"return_unique_pointer_nomove"});
}

struct NoCopyNoMove {
  std::string mtxt;
  NoCopyNoMove() : mtxt("DefaultConstructor") {}
  NoCopyNoMove(std::string_view mtxt_) : mtxt(mtxt_) {}
  NoCopyNoMove(const NoCopyNoMove&) = delete;
  NoCopyNoMove(NoCopyNoMove&&) = delete;

  NoCopyNoMove& operator=(const NoCopyNoMove &) = delete;
  NoCopyNoMove& operator=(NoCopyNoMove&&) = delete;
};

inline NoCopyNoMove* return_pointer_nocopy_nomove() {
  static NoCopyNoMove obj;
  obj.mtxt = "return_pointer_nocopy_nomove";
  return &obj;
}

inline std::shared_ptr<NoCopyNoMove> return_shared_pointer_nocopy_nomove() {
  return std::shared_ptr<NoCopyNoMove>(
      new NoCopyNoMove{"return_shared_pointer_nocopy_nomove"});
}

inline std::unique_ptr<NoCopyNoMove> return_unique_pointer_nocopy_nomove() {
  return std::unique_ptr<NoCopyNoMove>(
      new NoCopyNoMove{"return_unique_pointer_nocopy_nomove"});
}

}  // namespace clif_testing

#endif  // CLIF_TESTING_RETURN_VALUE_POLICY_H_
