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
#ifndef CLIF_TESTING_DERIVED_IN_OTHER_HEADER_CONCRETE_DERIVED_H_
#define CLIF_TESTING_DERIVED_IN_OTHER_HEADER_CONCRETE_DERIVED_H_

#include <iostream>

#include "clif/testing/derived_in_other_header/concrete_base.h"

namespace clif_testing {
namespace derived_in_other_header {

class ConcreteDerivedEmpty : public ConcreteBaseEmpty {
 public:
  // Printing from constructor & destructor for simple external validation.
  ConcreteDerivedEmpty() {
    std::cout << std::endl << "ConcreteDerivedEmpty+" << std::endl;
  }
  ~ConcreteDerivedEmpty() {
    std::cout << std::endl << "ConcreteDerivedEmpty-" << std::endl;
  }
  int Get() const { return 31607978; }
  int BaseGet(const ConcreteBaseEmpty& base) { return Get() + base.Get(); }
};

}  // namespace derived_in_other_header
}  // namespace clif_testing

#endif  // CLIF_TESTING_DERIVED_IN_OTHER_HEADER_CONCRETE_DERIVED_H_
