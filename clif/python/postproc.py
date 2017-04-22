# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Postprocessing utilities for CLIF.

Example usage:

For
bool Actor(const string& input, vector<int>* output);
use
def Actor(input: str) -> (ok: bool, output: list<int>) with ValueErrorOnFalse
to get clean list<int> for output and ValueError on error.
"""


def ValueErrorOnFalse(ok, *args):
  """Returns None / arg / (args,...) if ok."""
  if not isinstance(ok, bool):
    raise TypeError("Use ValueErrorOnFalse only on bool return value")
  if not ok:
    raise ValueError("CLIF wrapped call returned False")
  # Plain return args will turn 1 into (1,)  and None into () which is unwanted.
  if args:
    return args if len(args) > 1 else args[0]
  return None
