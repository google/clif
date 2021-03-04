// Copyright 2021 Google LLC
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

#ifndef CONCRETE_DERIVED_H
#define CONCRETE_DERIVED_H

#include "clif/testing/derived_in_other_header/concrete_base.h"
#include "clif/testing/derived_in_other_header/concrete_derived.h"
#include "third_party/pybind11/include/pybind11/smart_holder.h"

PYBIND11_SMART_HOLDER_TYPE_CASTERS(
    clif_testing::derived_in_other_header::ConcreteBaseEmpty);
PYBIND11_SMART_HOLDER_TYPE_CASTERS(
    clif_testing::derived_in_other_header::ConcreteDerivedEmpty);

#endif
