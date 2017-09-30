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
#ifndef CLIF_TESTING_T9_H_
#define CLIF_TESTING_T9_H_
#include "clif/python/types.h"

// Testing "capsule".
//
// We have some class hierarhies and test how they passed up/down those
// hierarhies with "class"/"capsule" intermix capabilities.

namespace t9 {

class Core {
 public:
  static bool IsDestructed() { return destructed_; }
  Core() : c_(12) { destructed_ = false; }
  ~Core() { destructed_ = true; }
  int CoreValue()
      { return c_; }
 protected:
  int c_;
 private:
  static bool destructed_;
};

class Base: public Core {
 public:
  virtual ~Base() {}
  virtual int Value() { return 1; }
};

class Derived: public Base {
 public:
  int Value() override { return 2; }
};

inline bool IsDerived(Base* c) { return c->Value() == 2; }

inline int CoreValue(Core* c) { return c->CoreValue(); }

class Abstract {
 public:
  virtual int Undef() = 0;
  virtual ~Abstract() {}
 private:
  std::unique_ptr<Core> core_;
};

class Concrete : public Abstract {
 public:
  int Undef() override { return 1; }
};

inline Abstract* NewAbstract() { return new Concrete; }

inline PyObject* ConversionFunctionCheck(PyObject* x) { return x; }

}  // namespace t9

#endif  // CLIF_TESTING_T9_H_
