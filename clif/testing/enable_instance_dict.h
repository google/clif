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
#ifndef CLIF_TESTING_ENABLE_INSTANCE_DICT_H_
#define CLIF_TESTING_ENABLE_INSTANCE_DICT_H_

namespace clif_testing {

class ConcreteEmptyNoDict {};
class ConcreteEmptyWithDict {};
class ConcreteEmptyWithDictFinal {};

// Exercises Py_BEGIN_ALLOW_THREADS, Py_END_ALLOW_THREADS.
class ConcreteNonTrivialDestructorWithDict {
 public:
  ConcreteNonTrivialDestructorWithDict() : raw_pointer{nullptr} {}
  ~ConcreteNonTrivialDestructorWithDict() {
    if (raw_pointer != nullptr) delete raw_pointer;
  }

 private:
  int* raw_pointer;
};

// N = No instance dict.
// D = Has instance dict.
struct BaseDD {};
struct DrvdDD : BaseDD {};
struct BaseND {};
struct DrvdND : BaseND {};
struct BaseDN {};
struct DrvdDN : BaseDN {};

}  // namespace clif_testing

#endif  // CLIF_TESTING_ENABLE_INSTANCE_DICT_H_
