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

struct _object;
typedef struct _object PyObject;

namespace t9 {

struct Core {
  Core() : c_(12) {}
  int CoreValue()
      { return c_; }
 protected:
  int c_;
};

struct Base: Core {
  virtual ~Base() {}
  virtual int Value()
      { return 1; }
};

struct Derived: Base {
  int Value() override
      { return 2; }
};

bool IsDerived(Base* c)
      { return c->Value() == 2; }

int CoreValue(Core* c)
      { return c->CoreValue(); }

struct Abstract {
  virtual int Undef() = 0;
  virtual ~Abstract() {}
 private:
  std::unique_ptr<Core> core_;
};

struct Concrete : Abstract {
  int Undef() override { return 1; }
};

Abstract* NewAbstract() { return new Concrete; }

PyObject* ConversionFunctionCheck(PyObject* x) { return x; }
}  // namespace t9

#endif  // CLIF_TESTING_T9_H_
