#ifndef CLIF_TESTING_ABSL_CORD_H_
#define CLIF_TESTING_ABSL_CORD_H_

#include <string>

#include "absl/strings/cord.h"

namespace clif_testing_absl_cord {

inline std::string PassAbslCord(const absl::Cord& c) { return std::string(c); }
inline absl::Cord ReturnAbslCord(const std::string& s) { return absl::Cord(s); }

}  // namespace clif_testing_absl_cord

#endif  // CLIF_TESTING_ABSL_CORD_H_
