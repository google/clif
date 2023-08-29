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
#ifndef CLIF_TESTING_SPECIAL_CLASSES_H_
#define CLIF_TESTING_SPECIAL_CLASSES_H_

namespace clif_testing {
namespace special_classes {

class Abstract {
  Abstract() {}
 public:
  static constexpr char KIND[] = "pure virtual";
  virtual ~Abstract() {}
  virtual int Future() = 0;
};

class Inconstructible {
  Inconstructible() {}
 public:
  static int F() { return 0; }
};

class NoDefaultConstructor {
  int a_;
 public:
  explicit NoDefaultConstructor(int a) : a_(a) {}
  int A() { return a_; }
};

// Class 'NoCopy' is not CLIF copyable because it does not contain a copy
// constructor or a copy assignment operator.
class NoCopy {
  int a_;
  NoCopy(const NoCopy&) = delete;
  NoCopy& operator=(const NoCopy&) = delete;
 public:
  explicit NoCopy(int a = 0) : a_(a) {}
  int A() { return a_; }
};

// Class 'NoMove' is not CLIF movable because it does not contain a move
// constructor or a move assignment operator.
class NoMove {
  int a_;
  NoMove(const NoMove&) = default;
  NoMove& operator=(const NoMove&) = default;
  NoMove(NoMove&&) = delete;
  NoMove& operator=(NoMove&&) = delete;
 public:
  explicit NoMove(int a = 0) : a_(a) {}
  int A() { return a_; }
};

}  // namespace special_classes
}  // namespace clif_testing

#endif  // CLIF_TESTING_SPECIAL_CLASSES_H_
