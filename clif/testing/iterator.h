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
#ifndef CLIF_TESTING_ITERATOR_H_
#define CLIF_TESTING_ITERATOR_H_

// A test class to expose a C++ iterator.
//
// It implements a toy ring buffer with value semantics (items must be copyable)
// It's using exceptions to demonstrate they are handled correctly by CLIF.

#include <array>

namespace clif_iterator_test {

template<typename T, size_t N>
class Ring {
 public:
  // Mimic std containers, so that Ring::const_iterator is a real thing.
  class const_iterator: public std::iterator<std::input_iterator_tag, T> {
   public:
    // CLIF requires both or neither of copy/move constructors and copy/move
    // copy assignment operators.
    const_iterator(const const_iterator&) = default;
    // Implicitly-declared copy assignment operator is deleted by the compiler
    // because of the non copy-assignable data member. Thus, "=default" does
    // not generate a copy assignment operator.
    const_iterator& operator=(const const_iterator&){}
    const_iterator(const_iterator&&) = default;
    const_iterator& operator=(const_iterator&&) = default;
    const_iterator(): offset_(0), start_(nullptr) {}
    const_iterator(size_t offset, const T* const start)
        : offset_(offset), start_(start) {}
    const_iterator& operator++() {
      offset_ = (1 + offset_) % N;
      return *this;
    }
    const_iterator operator++(int) {
      const_iterator it(offset_, start_);
      ++*this;
      return it;
    }
    bool operator==(const_iterator o) const {
      return start_ == o.start_ && offset_ == o.offset_;
    }
    bool operator!=(const_iterator o) const {
      return start_ != o.start_ || offset_ != o.offset_;
    }
    const T& operator*() const { return *(start_+offset_); }

   private:
    size_t offset_;  // Ring<T>::data_ current index.
    const T* const start_;  // Pointer to Ring<T>::data_[0].
  };

  struct Full {};
  struct Empty {};

  Ring() : get_(N), put_(0) {}
  void clear() { get_ = N; put_ = 0; }

  T pop() {
    if (get_ == N) throw Empty();
    size_t i = get_;
    get_next();
    return data_[i];
  }
  void push(T v) {
    if (put_ == get_) throw Full();
    data_[put_] = v;
    put_next();
  }
  const_iterator begin() const { return const_iterator(get_, &data_[0]); }
  const_iterator end() const { return const_iterator(put_, &data_[0]); }
  bool operator!() const { return get_ == N; }
  operator bool() const { return get_ != N; }

 private:
  inline void get_next() {
    get_ = (1 + get_) % N;
    if (get_ == put_) {
      get_ = N;
      put_ = 0;
    }
  }
  inline void put_next() {
    if (get_ == N) get_ = put_;
    put_ = (1 + put_) % N;
  }

 private:
  std::array<T, N> data_;
  size_t get_, put_;  // data_ index for next pop/push operation.
};
}  // namespace clif_iterator_test

#endif  // CLIF_TESTING_ITERATOR_H_
