#ifndef CLIF_TESTING_FINAL_NESTED_H_
#define CLIF_TESTING_FINAL_NESTED_H_

namespace clif_testing_final_nested {

struct Outer  // final  // UNCOMMENT to reproduce b/212441720
{
  struct Inner {};
};

}  // namespace clif_testing_final_nested

#endif  // CLIF_TESTING_FINAL_NESTED_H_
