/*
 * Copyright 2020 Google LLC
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
#ifndef CLIF_TESTING_DERIVED_IN_OTHER_HEADER_SHARED_UNIQUE_INTEROP_H_
#define CLIF_TESTING_DERIVED_IN_OTHER_HEADER_SHARED_UNIQUE_INTEROP_H_

#include <iostream>
#include <memory>

#include "clif/testing/derived_in_other_header/concrete_base.h"
#include "clif/testing/derived_in_other_header/concrete_derived.h"
#include "clif/testing/derived_in_other_header/virtual_base.h"
#include "clif/testing/derived_in_other_header/virtual_derived.h"

namespace clif_testing {
namespace derived_in_other_header {

inline std::unique_ptr<ConcreteBaseEmpty>
make_unique_concrete_derived_empty_up_cast() {
  // b/175568410: Undefined Behavior:
  // ConcreteDerivedEmpty destructor does not run.
  return std::unique_ptr<ConcreteDerivedEmpty>(new ConcreteDerivedEmpty);
}

inline std::shared_ptr<ConcreteBaseEmpty>
make_shared_concrete_derived_empty_up_cast(bool use_custom_deleter = false) {
  if (use_custom_deleter) {
    return std::shared_ptr<ConcreteDerivedEmpty>(
        new ConcreteDerivedEmpty, [](ConcreteDerivedEmpty *p) { delete p; });
  }
  return std::shared_ptr<ConcreteDerivedEmpty>(new ConcreteDerivedEmpty);
}

inline int pass_unique_concrete_base_empty(
    std::unique_ptr<ConcreteBaseEmpty> cbe) {
  return cbe->Get();
}

inline int pass_shared_concrete_base_empty(
    std::shared_ptr<ConcreteBaseEmpty> cbe) {
  return cbe->Get();
}

inline std::unique_ptr<VirtualBaseEmpty>
make_unique_virtual_derived_empty_up_cast() {
  // Well-defined behavior because VirtualDerivedEmpty has a virtual destructor.
  return std::unique_ptr<VirtualDerivedEmpty>(new VirtualDerivedEmpty);
}

inline std::shared_ptr<VirtualBaseEmpty>
make_shared_virtual_derived_empty_up_cast(bool use_custom_deleter = false) {
  if (use_custom_deleter) {
    return std::shared_ptr<VirtualDerivedEmpty>(
        new VirtualDerivedEmpty, [](VirtualDerivedEmpty *p) { delete p; });
  }
  return std::shared_ptr<VirtualDerivedEmpty>(new VirtualDerivedEmpty);
}

inline int pass_unique_virtual_base_empty(
    std::unique_ptr<VirtualBaseEmpty> vbe) {
  return vbe->Get();
}

inline int pass_shared_virtual_base_empty(
    std::shared_ptr<VirtualBaseEmpty> vbe) {
  return vbe->Get();
}

}  // namespace derived_in_other_header
}  // namespace clif_testing

#endif  // CLIF_TESTING_DERIVED_IN_OTHER_HEADER_SHARED_UNIQUE_INTEROP_H_
