#ifndef CLIF_TESTING_OVERLOAD_H_
#define CLIF_TESTING_OVERLOAD_H_

#include <string>
#include <functional>

// Test for an overload pattern that caused CLIF to segfault
// (b/133620699)
namespace overload {

std::unique_ptr<int> Factory();

using ClientFactory = std::function<decltype(Factory)>;

class Accessor {
 public:
  virtual ~Accessor() = default;

  static bool Create(const ClientFactory& stub_creator = Factory) {
    return true;
  }

  static bool Create(const std::string& address) {
    return true;
  }
};

}  // namespace overload

#endif  // CLIF_TESTING_OVERLOAD_H_
