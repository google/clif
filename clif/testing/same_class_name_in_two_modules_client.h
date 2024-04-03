#ifndef CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_CLIENT_H_
#define CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_CLIENT_H_

#include "clif/testing/same_class_name_in_two_modules_alpha.h"
#include "clif/testing/same_class_name_in_two_modules_bravo.h"

namespace clif_testing_same_class_name_in_two_modules_client {

inline clif_testing_same_class_name_in_two_modules_alpha::Smith
ReturnAlphaSmith() {
  return clif_testing_same_class_name_in_two_modules_alpha::Smith();
}

inline clif_testing_same_class_name_in_two_modules_bravo::Smith
ReturnBravoSmith() {
  return clif_testing_same_class_name_in_two_modules_bravo::Smith();
}

}  // namespace clif_testing_same_class_name_in_two_modules_client

#endif  // CLIF_TESTING_SAME_CLASS_NAME_IN_TWO_MODULES_CLIENT_H_
