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
#ifndef CLIF_TESTING_EXTEND_METHODS_H_
#define CLIF_TESTING_EXTEND_METHODS_H_

namespace clif_testing {

class ConcreteHolder {
 public:
  ConcreteHolder() : value_{0} {}
  int Get() const { return value_; }
  void Set(int value) { value_ = value; }

 private:
  int value_;
};

class VirtualBaseHolder {
 public:
  virtual ~VirtualBaseHolder() {}
  virtual int Get() const = 0;
  virtual void Set(int value) = 0;
};

class VirtualDerivedHolder : public VirtualBaseHolder {
 public:
  VirtualDerivedHolder() : value_{0} {}
  int Get() const override { return value_; }
  void Set(int value) override { value_ = value; }

 private:
  int value_;
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_EXTEND_METHODS_H_
