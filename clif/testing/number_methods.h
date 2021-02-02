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
#ifndef CLIF_TESTING_NUMBER_METHODS_H_
#define CLIF_TESTING_NUMBER_METHODS_H_

#include <cmath>
#include <utility>

namespace clif_testing {

class Number {
 public:
  Number() = default;
  Number(float n): value(n) {}

  Number& operator+=(const Number& other) {
    value = value + other.value;
    return *this;
  }

  Number& operator-=(const Number& other) {
    value = value - other.value;
    return *this;
  }

  Number& operator*=(const Number& other) {
    value = value * other.value;
    return *this;
  }

  Number& operator/=(const Number& other) {
    value = value / other.value;
    return *this;
  }

  Number& operator%=(const Number& other) {
    value = remainder(value, other.value);
    return *this;
  }

  Number& operator<<=(int n) {
    value = static_cast<int>(value) << n;
    return *this;
  }

  Number& operator>>=(int n) {
    value = static_cast<int>(value) >> n;
    return *this;
  }

  Number& operator&=(const Number& other) {
    value = static_cast<int>(value) & static_cast<int>(other.value);
    return *this;
  }

  Number& operator^=(const Number& other) {
    value = static_cast<int>(value) ^ static_cast<int>(other.value);
    return *this;
  }

  Number& operator|=(const Number& other) {
    value = static_cast<int>(value) | static_cast<int>(other.value);
    return *this;
  }

  Number negative() const {
    Number number(-value);
    return number;
  }

  Number positive() const {
    Number number(value);
    return number;
  }

  Number abs() const {
    Number number(std::abs(value));
    return number;
  }

  Number operator~() const {
    Number number(~static_cast<int>(value));
    return number;
  }

  Number operator<<(int n) const {
    Number number(static_cast<int>(value) << n);
    return number;
  }

  Number operator>>(int n) const {
    Number number(static_cast<int>(value) >> n);
    return number;
  }

  Number operator&(const Number& other) const {
    Number number(static_cast<int>(value) & static_cast<int>(other.value));
    return number;
  }

  Number operator^(const Number& other) const {
    Number number(static_cast<int>(value) ^ static_cast<int>(other.value));
    return number;
  }

  Number operator|(const Number& other) const {
    Number number(static_cast<int>(value) | static_cast<int>(other.value));
    return number;
  }

  Number& inplace_floor_division(const Number& other) {
    value = floor(value / other.value);
    return *this;
  }

  Number floor_division(const Number& other) {
    Number number;
    number.value = floor(value / other.value);
    return number;
  }

  Number& inplace_power(const Number* const exponent,
                        const Number* const modulus = nullptr) {
    if (modulus) {
      value = (remainder(pow(value, exponent->value), modulus->value));
    } else {
      value = pow(value, exponent->value);
    }
    return *this;
  }

  Number power(
      const Number* const exponent,
      const Number* const modulus = nullptr) {
    if (modulus) {
      return Number(remainder(pow(value, exponent->value),
                    modulus->value));
    } else {
      return Number(pow(value, exponent->value));
    }
  }

  std::pair<Number, Number> divmod(const Number& other) {
    Number n1, n2;
    n1.value = floor(value / other.value);
    n2.value = remainder(value, other.value);
    return std::make_pair(n1, n2);
  }

  Number my_mul(const Number& other) {
    Number number;
    // To differentiate this method with operator* overloading.
    number.value = value * other.value * 10;
    return number;
  }

  operator bool() const { return static_cast<bool>(value); }
  operator int() const { return static_cast<int>(value); }
  operator float() const { return value; }

  float value;
};

inline Number operator+(const Number& a, const Number& b) {
  Number number;
  number.value = a.value + b.value;
  return number;
}

inline Number operator-(const Number& a, const Number& b) {
  Number number;
  number.value = a.value - b.value;
  return number;
}

inline Number operator*(const Number& a, const Number& b) {
  Number number;
  number.value = a.value * b.value;
  return number;
}

inline Number operator/(const Number& a, const Number& b) {
  Number number;
  number.value = a.value / b.value;
  return number;
}

inline Number operator%(const Number& a, const Number& b) {
  Number number;
  number.value = remainder(a.value, b.value);
  return number;
}

}  // namespace clif_testing

#endif  // CLIF_TESTING_SEQUENCE_METHODS_H_
