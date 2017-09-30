// Copyright 2017 Google Inc.
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

#include "wrapfunc/wrapfunc.h"
#include "wrappod/wrappod.h"

namespace {
int State = 0xDEAD;
}

namespace clif_example {
namespace wrapfunc {

void ResetState() {
  ::State = 0;
}

void SetState(int a) {
  ::State = a;
}

void SetState(int a, int b) {
  ::State = a + b;
}

void SetState(const clif_example::wrappod::MyClass& s) {
  ::State = s.a;
}

int GetState() {
  return ::State;
}

// Clif does not make  any guarantees when calling functions which take raw
// pointer args. See the function Delete below. Behavior here is expected.
void GetState(clif_example::wrappod::MyClass *s) {
  s->a = ::State;
}

}  // namespace wrapfunc
}  // namespace clif_example
