#ifndef CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_BRAVO_H_
#define CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_BRAVO_H_

#include <string>

namespace clif_testing_same_class_name_in_two_modules_bravo {

class Smith {
 public:
  static std::string WhereIsHome() { return "I live in Bravoville."; }
};

}  // namespace clif_testing_same_class_name_in_two_modules_bravo

#endif  // CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_BRAVO_H_
