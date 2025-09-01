# Copyright 2025 PhonePe Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import TestCase

from phonepe.sdk.pg.common.utils.dict_utils import merge_dict


class TestUtils(TestCase):
    def test_merge_dict(self):
        # both none
        result = merge_dict(None, None)
        assert result == {}

        # one of them is none
        dict_with_vals = {"a": 1, "b": 2}
        result = merge_dict(None, dict_with_vals)
        assert result == dict_with_vals
        result = merge_dict(dict_with_vals, None)
        assert result == dict_with_vals

        # same copy
        result = merge_dict(dict_with_vals, dict_with_vals)
        assert result == dict_with_vals

        # diff vals
        dict_with_diff_vals = {"c": 3, "d": 4}
        expected_result = {"a": 1, "b": 2, "c": 3, "d": 4}
        result = merge_dict(dict_with_vals, dict_with_diff_vals)
        assert result == expected_result

        # overlapping vals
        dict_with_overlapping_vals = {"b": -1, "c": 3}
        expected_result = {"a": 1, "b": -1, "c": 3}
        result = merge_dict(dict_with_vals, dict_with_overlapping_vals)
        assert result == expected_result

        dict_with_none = {"val1": None}
        dict_without_none = {"val1": "asd"}
        result = merge_dict(dict_with_none, dict_without_none)
        assert result == {"val1": "asd"}
        result = merge_dict(dict_without_none, dict_with_none)
        assert result == {"val1": "asd"}
