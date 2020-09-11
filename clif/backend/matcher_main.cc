// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <fstream>
#include <functional>
#include <string>
#include <vector>

#include "clif/backend/matcher.h"
#include "clif/protos/ast.pb.h"
#include "llvm/Support/raw_ostream.h"

llvm::cl::opt<bool> FLAGS_text_protos(
    "text_protos",
    llvm::cl::desc("Treat input and output protos in text format."),
    llvm::cl::init(false));
llvm::cl::opt<std::string> FLAGS_input_file(
    "input_file",
    llvm::cl::desc("Name of a proto file to match."),
    llvm::cl::init(""));
llvm::cl::opt<std::string> FLAGS_output_file(
    "output_file",
    llvm::cl::desc("Name of a file to write the matched proto."),
    llvm::cl::init(""));
llvm::cl::list<std::string> FLAGS_compiler_args(
    llvm::cl::Sink,
    llvm::cl::desc("<compiler arguments>..."));

using clif::protos::AST;
using clif::ClifMatcher;

int main(int argc, char* argv[]) {
  std::string output_file;
  std::string input_file;
  for (int i = 1; i < argc; i++) {
    llvm::StringRef argv_i(argv[i]);
    if (!argv_i.startswith("--") && argv_i.endswith(".ipb")) {
      input_file = argv_i;
      // llvm considers an ipb file a linker input and will complain
      // if it appears, so remove it from the list.
      memmove(argv + i, argv + i + 1, (argc - i - 1) * sizeof(char *));
      argc -= 1;
      i--;
    } else if (i < argc - 1 && argv_i == "-o") {
      output_file = argv[i + 1];
    }
  }

  llvm::cl::ParseCommandLineOptions(argc, argv);
  // TODO: Remove --input_file and --output_file when they
  // are no longer passed by blaze or the py_clif_cc rule.
  if (!FLAGS_output_file.empty())
    output_file = FLAGS_output_file;
  if (!FLAGS_input_file.empty())
    input_file = FLAGS_input_file;

  if (input_file.empty()) {
    input_file = "/dev/stdin";
  }
  if (output_file.empty()) {
    output_file = "/dev/stdout";
  }

  AST input_proto;
  std::ifstream input_stream(input_file.c_str(),
                             std::fstream::in |
                             std::fstream::binary);
  if (!input_stream.is_open()) {
    llvm::errs() << "Couldn't open input file " << input_file;
    return 1;
  }
  if (!input_proto.ParseFromIstream(&input_stream)) {
    llvm::errs() << "Couldn't parse input file " << input_file;
    return 1;
  }
  input_stream.close();

  ClifMatcher matcher;
  AST output_proto;
  std::vector<std::string> args;
  args.push_back(argv[0]);
  for (const auto &arg : FLAGS_compiler_args) {
    args.push_back(arg);
  }
  // Tell clang this is C++. The ipb doesn't have the right extension.
  args.push_back("-x");
  args.push_back("c++");
  bool matched = matcher.CompileMatchAndSet(args,
                                            input_file,
                                            input_proto,
                                            &output_proto);

  std::ofstream output_stream;
  output_stream.open(output_file,
                     std::fstream::out |
                     std::fstream::trunc |
                     std::fstream::binary);
  if (!output_stream.is_open()) {
    llvm::errs() << "Couldn't open output file " << output_file;
    return 1;
  }
  if (!output_proto.SerializeToOstream(&output_stream)) {
    llvm::errs() << "Couldn't serialize to output file " << output_file;
    return 1;
  }
  return matched ? 0 : 1;
}
