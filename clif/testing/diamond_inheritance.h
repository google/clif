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
#ifndef CLIF_TESTING_DIAMOND_INHERITANCE_H_
#define CLIF_TESTING_DIAMOND_INHERITANCE_H_

namespace inheritance {

template <class T>
class Base {
 public:
  T GetBaseValue() { return i_; }

  void SetBaseValue(T i) { i_ = i; }

 private:
  T i_;
};

template <class T>
class Derived1 : virtual public Base<T> {};

template <class T>
class Derived2 : virtual public Base<T> {};

template <class T>
class Derived3 : public Derived1<T>, public Derived2<T> {};

typedef Derived3<int> Derived3_int;

}  // namespace inheritance

#endif  // CLIF_TESTING_DIAMOND_INHERITANCE_H_
