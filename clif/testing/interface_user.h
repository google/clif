// This library declares functions and types that consume the types declared
// in `interface_declarer.h`. It exists to test that the CLIF generated C++
// headers for `interface_declarer.h` are properly consumed when generating the
// CLIF library associated with this C++ library.

#ifndef CLIF_TESTING_INTERFACE_USER_H_
#define CLIF_TESTING_INTERFACE_USER_H_

#include "clif/testing/interface_declarer.h"

namespace clif_testing_interface_user {

// Returns a new container containing twice the value of the given container.
template <typename T>
clif_testing_interface_declarer::ValueContainer<T> DoubleValue(
    const clif_testing_interface_declarer::ValueContainer<T>& value_container) {
  return clif_testing_interface_declarer::ValueContainer<T>(
      value_container.GetValue() * 2);
}

// Sample inheriting class that adds additional functionality to a
// `ValueContainer`.
template <typename T>
class DoublingContainer
    : public clif_testing_interface_declarer::ValueContainer<T> {
 public:
  explicit DoublingContainer(T value)
      : clif_testing_interface_declarer::ValueContainer<T>(std::move(value)) {}

  // Doubles the value stored in this container.
  void DoubleSelf() { this->SetValue(this->GetValue() * 2); }
};

}  // namespace clif_testing_interface_user

#endif  // CLIF_TESTING_INTERFACE_USER_H_
