// This library declares types that are CLIF-wrapped in interface_declarer.clif
// by using the `interface` keyword in the class definition.

#ifndef CLIF_TESTING_INTERFACE_DECLARER_H_
#define CLIF_TESTING_INTERFACE_DECLARER_H_

#include <utility>

namespace clif_testing_interface_declarer {

// Sample inheritable class for a simple value container.
template <typename T>
class ValueContainer {
 public:
  explicit ValueContainer(T value) : value_(std::move(value)) {}

  virtual ~ValueContainer() = default;

  // Gets the value stored in this container.
  const T& GetValue() const { return value_; }

  // Sets the value stored in this container.
  void SetValue(T value) { value_ = std::move(value); }

 private:
  T value_;
};

}  // namespace clif_testing_interface_declarer

#endif  // CLIF_TESTING_INTERFACE_DECLARER_H_
