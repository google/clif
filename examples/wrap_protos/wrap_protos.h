/*
 * Copyright 2017 Google Inc.
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
#ifndef CLIF_EXAMPLES_WRAP_PROTOS_WRAP_PROTOS_H_
#define CLIF_EXAMPLES_WRAP_PROTOS_WRAP_PROTOS_H_

#include "wrap_protos/protos/sample.pb.h"

namespace clif_example {
namespace wrap_protos {

// Takes a pointer to a proto message as argument.
inline void DefaultInitMyMessage(protos::MyMessage* s) {
  s->set_name("default");
  protos::EmbeddedMsg* msg = s->mutable_msg();
  msg->add_id(0xdef);
}

class ProtoManager {
 public:
  ProtoManager() : sample_up_(new protos::MyMessage) {
    DefaultInitMyMessage(sample_up_.get());
  }

  // Returns a non-const pointer to a proto message.
  protos::MyMessage *GetMyMessage() {
    return sample_up_.get();
  }

 private:
  std::unique_ptr<protos::MyMessage> sample_up_;
};

inline protos::MyMessage MakeMyMessageFromNested(
    const protos::MyMessage::Nested& nested) {
  protos::MyMessage msg;
  msg.set_name("from_nested");
  protos::MyMessage::Nested* n = msg.mutable_nested();
  n->set_value(nested.value());
  return msg;
}

inline protos::MyMessage MakeMyMessageFromNestedEnum(
    protos::MyMessage::Nested::NestedEnum value) {
  protos::MyMessage msg;
  msg.set_name("from_nested_enum");
  protos::MyMessage::Nested* n = msg.mutable_nested();
  n->set_value(value);
  return msg;
}

}  // namespace wrap_protos
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_WRAP_PROTOS_WRAP_PROTOS_H_
