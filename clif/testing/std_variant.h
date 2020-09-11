// Copyright 2019 Abseil Authors and Google LLC.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef THIRD_PARTY_CLIF_TESTING_STD_VARIANT_H_
#define THIRD_PARTY_CLIF_TESTING_STD_VARIANT_H_

#include <initializer_list>
#include <memory>
#include <optional>
#include <variant>

#include "clif/python/types.h"

namespace clif_test {

template <typename... T>
int VariantIndex(const ::std::variant<T...>& v) {
  return v.index();
}

template <typename... T>
std::variant<T...> Identity(const ::std::variant<T...>& v) {
  return v;
}

struct WithDirectConv {
  int value;
};

struct WithOptionalConv {
  int value;
};

struct WithUniquePtrConv {
  int value;
};

inline int GetDirect(const ::std::variant<WithDirectConv>& v) {
  return ::std::get<0>(v).value;
}

inline int GetOptional(const ::std::variant<WithOptionalConv>& v) {
  return ::std::get<0>(v).value;
}

inline int GetUniquePtr(const ::std::variant<WithUniquePtrConv>& v) {
  return ::std::get<0>(v).value;
}

// CLIF use `::clif_test::WithDirectConv` as WithDirectConv
// CLIF use `::clif_test::WithOptionalConv` as WithOptionalConv
// CLIF use `::clif_test::WithUniquePtrConv` as WithUniquePtrConv
// These conversions convert Python integers to integer wrapper structs, but
// also modifies the integer value n to n + 1. This is purely for test purpose.
bool Clif_PyObjAs(PyObject* obj, WithDirectConv* c);
bool Clif_PyObjAs(PyObject* obj, ::std::optional<WithOptionalConv>* c);
bool Clif_PyObjAs(PyObject* obj, std::unique_ptr<WithUniquePtrConv>* c);

}  // namespace clif_test

#endif  // THIRD_PARTY_CLIF_TESTING_STD_VARIANT_H_
