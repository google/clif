#ifndef THIRD_PARTY_CLIF_TESTING_FINAL_H_
#define THIRD_PARTY_CLIF_TESTING_FINAL_H_

#include <Python.h>

namespace clif_testing_final {

// This emulates an object that can behave as a `Final` by implementing
// `as_clif_testing_final_Final`. This is used e.g. for CLIF/SWIG interop.
struct SwigFinal {
  PyObject* as_clif_testing_final_Final() {
    void* vptr = static_cast<void*>(this);
    return PyCapsule_New(vptr, "::clif_testing_final::Final", nullptr);
  }
};

struct Final final {};

inline void TakesFinal(Final*) {}

}  // namespace clif_testing_final

#endif  // THIRD_PARTY_CLIF_TESTING_FINAL_H_
