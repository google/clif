# Copyright 2023 Google LLC.
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

"""Decorators for handling exceptions in callbacks."""

import sys
import traceback

from absl import logging


def print_and_clear(*, substitute_return_value, file=None):
  """Test & recommended use in ../testing/python/callback_test.py."""

  def _(callback):
    def _(*args, **kwargs):
      """Decorator implementation."""
      try:
        return callback(*args, **kwargs)
      except Exception:  # pylint: disable=broad-exception-caught
        sys.stdout.flush()
        sys.stderr.flush()
        traceback.print_exc(file=file)
        flush = getattr(file, "flush", None)
        if flush:
          flush()
        else:
          sys.stdout.flush()
          sys.stderr.flush()
      return substitute_return_value

    return _

  return _


def log_and_clear(*, substitute_return_value):
  """Test & recommended use in ../testing/python/callback_test.py."""

  def _(callback):
    def _(*args, **kwargs):
      """Decorator implementation."""
      try:
        return callback(*args, **kwargs)
      except Exception:  # pylint: disable=broad-exception-caught
        for line in traceback.format_exc().splitlines():
          logging.error(line)
      return substitute_return_value

    return _

  return _
