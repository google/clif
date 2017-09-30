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
// C++ declarations for clif backend tests.  Not necessarily Google
// style compliant nor ever actually compiled into object code.
#ifndef CLIF_BACKEND_VERSIONED_SMART_PTR_TEST_H_
#define CLIF_BACKEND_VERSIONED_SMART_PTR_TEST_H_

// Header file for versioned smart pointers' test. Versioned smart pointer is
// not defined in "./test.h" because we do not want to influence
// std::unique_ptr's functionality used in "./test.h".

namespace std {
// Define versioned unique_ptr.
inline namespace __google {
template <class T>
class unique_ptr {};
}  // namespace __google
}  // namespace std

std::unique_ptr<int> f() { return std::unique_ptr<int>(); }

#endif  // CLIF_BACKEND_VERSIONED_SMART_PTR_TEST_H_
