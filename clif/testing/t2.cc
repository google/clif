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

#include <stdio.h>
#include "clif/testing/t2.h"

int K::i1() const { return i_+1; }

bool takeK(const K& k) { return k.i1() == K::C; }

void k_modify(std::shared_ptr<K> k, int v) { k->set(v); }

std::unique_ptr<K> k_return() { return std::unique_ptr<K>(); }

bool Derived::has(int k) {
  int i = get();
  if (i <= j) return i <= k && k <= j;
  return false;
}

std::vector<std::unique_ptr<NoCopy>> all_nocopy_holds() {
  std::vector<std::unique_ptr<NoCopy>> r;
  for (int i = 1; i < 4; ++i) {
    std::unique_ptr<NoCopy> v(new NoCopy(i));
    r.push_back(std::move(v));
  }
  return r;
}

std::unique_ptr<std::vector<Nested>> vector_inside_unique_ptr() {
  std::unique_ptr<std::vector<Nested>> v(new std::vector<Nested>);
  return v;
}

void take_nocopy_class(MovableButUncopyable*) {
}

constexpr char Abstract::KIND[];
