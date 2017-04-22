/*
 * Copyright 2017 Google Inc.
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
#ifndef CLIF_EXAMPLES_WRAPFUNC_WRAPFUNC_H_
#define CLIF_EXAMPLES_WRAPFUNC_WRAPFUNC_H_

#include <memory>

namespace clif_example {
namespace wrappod {
class MyClass;
}  // namespace wrappod
}  // namespace clif_example

namespace clif_example {
namespace wrapfunc {

void ResetState();

// Sets the state to a.
void SetState(int a);

// Sets the state to a + b
void SetState(int a, int b);

// Sets the state to s.a
void SetState(const clif_example::wrappod::MyClass &s);

// Returns the state
int GetState();

/*
The following conflicts with "int GetState();" if we want to provide a wrapper
for GetState returning an int.
void GetState(int *a);
*/

// Stores the state in s.a
void GetState(clif_example::wrappod::MyClass *s);

}  // namespace wrapfunc
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_WRAPFUNC_WRAPFUNC_H_
