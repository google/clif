/*
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef CLIF_TESTING_STD_CONTAINERS_STR_BYTES_H_
#define CLIF_TESTING_STD_CONTAINERS_STR_BYTES_H_

#include <functional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace clif_testing_std_containers_str_bytes {
namespace helpers {

inline int sum_string_size(const std::vector<std::string>& v) {
  int n = 0;
  for (const auto& e : v) {
    n += e.size();
  }
  return n;
}

}  // namespace helpers

static const char* kUC16 = "\u039E";      // Any 16-bit code point (Greek Xi).
static const char* kUC32 = "\U0001FAA2";  // Any 32-bit code point (Knot).
static const char* kX80 = "\x80";  // Malformed UTF-8: sensitive to accidental
                                   // decode-encode cycles.

using VectorString = std::vector<std::string>;

inline VectorString ReturnVectorString(bool return_bytes) {
  if (return_bytes) {
    return VectorString({kX80});
  }
  return VectorString({kUC32});
}

inline int PassVectorString(const VectorString& v) {
  return helpers::sum_string_size(v);
}

inline bool PassCallbackPassVectorString(
    std::function<bool(const VectorString&)> f) {
  VectorString v{""};
  return f(v);
}

inline int PassCallbackReturnVectorString(std::function<VectorString()> f) {
  VectorString v = f();
  return helpers::sum_string_size(v);
}

struct VirtualBaseVectorString {
  virtual ~VirtualBaseVectorString() = default;
  virtual bool PassListStr(const VectorString&) = 0;
  virtual bool PassListBytes(const VectorString&) = 0;
  virtual VectorString ReturnListStr() = 0;
  virtual VectorString ReturnListBytes() = 0;
};

inline bool CallVirtualPassList(VirtualBaseVectorString* vb,
                                std::string_view fname) {
  if (fname == "PassListStr") {
    return vb->PassListStr(VectorString{kUC32});
  }
  return vb->PassListBytes(VectorString{kX80});
}

inline int CallVirtualReturnList(VirtualBaseVectorString* vb,
                                 std::string_view fname) {
  VectorString v;
  if (fname == "ReturnListStr") {
    v = vb->ReturnListStr();
  } else {
    v = vb->ReturnListBytes();
  }
  return helpers::sum_string_size(v);
}

using PairString = std::pair<std::string, std::string>;

inline PairString ReturnPairString() { return PairString({"first", "second"}); }

inline int PassPairString(const PairString& p) {
  return p.first.size() + p.second.size();
}

inline bool PassCallbackPassPairString(
    std::function<bool(const PairString&)> f) {
  PairString p{"", ""};
  return f(p);
}

inline int PassCallbackReturnPairString(std::function<PairString()> f) {
  PairString p = f();
  return PassPairString(p);
}

struct VirtualBasePairString {
  virtual ~VirtualBasePairString() = default;
  virtual bool PassTupleStrStr(const PairString&) = 0;
  virtual bool PassTupleBytesBytes(const PairString&) = 0;
  virtual bool PassTupleStrBytes(const PairString&) = 0;
  virtual bool PassTupleBytesStr(const PairString&) = 0;
  virtual PairString ReturnTupleStrStr() = 0;
  virtual PairString ReturnTupleBytesBytes() = 0;
  virtual PairString ReturnTupleStrBytes() = 0;
  virtual PairString ReturnTupleBytesStr() = 0;
};

inline bool CallVirtualPassTuple(VirtualBasePairString* vb,
                                 std::string_view fname) {
  PairString p{"", ""};
  if (fname == "PassTupleStrStr") {
    return vb->PassTupleStrStr(p);
  }
  if (fname == "PassTupleBytesBytes") {
    return vb->PassTupleBytesBytes(p);
  }
  if (fname == "PassTupleStrBytes") {
    return vb->PassTupleStrBytes(p);
  }
  return vb->PassTupleBytesStr(p);
}

inline int CallVirtualReturnTuple(VirtualBasePairString* vb,
                                  std::string_view fname) {
  PairString p;
  if (fname == "ReturnTupleStrStr") {
    p = vb->ReturnTupleStrStr();
  } else if (fname == "ReturnTupleBytesBytes") {
    p = vb->ReturnTupleBytesBytes();
  } else if (fname == "ReturnTupleStrBytes") {
    p = vb->ReturnTupleStrBytes();
  } else {
    p = vb->ReturnTupleBytesStr();
  }
  return PassPairString(p);
}

using NestedPairString = std::pair<PairString, PairString>;

inline NestedPairString ReturnNestedPairString() {
  return NestedPairString(
      {PairString({kUC32, kX80}), PairString({kX80, kUC16})});
}

inline int PassNestedPairString(const NestedPairString& np) {
  return np.first.first.size() + np.first.second.size() +
         np.second.first.size() + np.second.second.size();
}

inline bool PassCallbackPassNestedPairString(
    std::function<bool(const NestedPairString&)> f) {
  NestedPairString np({PairString({kUC32, kX80}), PairString({kUC16, kX80})});
  return f(np);
}

inline int PassCallbackReturnNestedPairString(
    std::function<NestedPairString()> f) {
  NestedPairString np = f();
  return PassNestedPairString(np);
}

struct VirtualBaseNestedPairString {
  virtual ~VirtualBaseNestedPairString() = default;
  virtual bool PassNestedTuple(const NestedPairString&) = 0;
  virtual NestedPairString ReturnNestedTuple() = 0;
};

inline bool CallVirtualPassNestedTuple(VirtualBaseNestedPairString* vb) {
  NestedPairString np({PairString({kUC32, kUC16}), PairString({kX80, kX80})});
  return vb->PassNestedTuple(np);
}

inline int CallVirtualReturnNestedTuple(VirtualBaseNestedPairString* vb) {
  NestedPairString np = vb->ReturnNestedTuple();
  return PassNestedPairString(np);
}

}  // namespace clif_testing_std_containers_str_bytes

#endif  // CLIF_TESTING_STD_CONTAINERS_STR_BYTES_H_
