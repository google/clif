#ifndef CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_ALPHA_H_
#define CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_ALPHA_H_

#include <string>

namespace clif_testing_same_class_name_in_two_modules_alpha {

class Smith {
 public:
  static std::string WhereIsHome() { return "I live in Alphaville."; }
};

}  // namespace clif_testing_same_class_name_in_two_modules_alpha

#endif  // CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_ALPHA_H_
