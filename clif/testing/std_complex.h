#ifndef CLIF_TESTING_STD_COMPLEX_H_
#define CLIF_TESTING_STD_COMPLEX_H_

#include <complex>
#include <cstdint>

namespace clif_test {

template <typename T>
class StdComplex {
 public:
  static std::complex<T> Zero() { return std::complex<T>(0, 0); }
  static std::complex<T> One() { return std::complex<T>(1, 0); }
  static std::complex<T> i() { return std::complex<T>(0, 1); }

  static std::complex<T> Multiply(std::complex<T> a, std::complex<T> b) {
    return a * b;
  }
};

}  // namespace clif_test

#endif  // CLIF_TESTING_STD_COMPLEX_H_
