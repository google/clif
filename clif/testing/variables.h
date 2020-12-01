#ifndef THIRD_PARTY_CLIF_TESTING_VARIABLES_H_
#define THIRD_PARTY_CLIF_TESTING_VARIABLES_H_

#include <complex>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace clif_testing {
namespace variables {

const int kMyConstInt = 42;
const int kMyConstIntRenamed = 123;
const float kMyConstFloat = 15.0;
const double kMyConstDouble = 20.0;
const bool kMyConstBool = true;
const std::complex<float> kMyConstComplex(1, 0);
const std::vector<int> kMyConstIntArray{ 0, 10, 20, 30, 40 };
const std::pair<int, int> kMyConstPair{ 0, 10 };
const std::unordered_map<int, int> kMyConstMap({{1, 10}, {2, 20}, {3, 30}});
const std::unordered_set<int> kMyConstSet({1, 2, 3});

}  // namespace variables
}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_VARIABLES_H_
