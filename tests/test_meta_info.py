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

from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo


class TestMetaInfo(TestCase):

    def test_all_15_udf_fields_can_be_set(self):
        meta = MetaInfo(
            udf1="v1", udf2="v2", udf3="v3", udf4="v4", udf5="v5",
            udf6="v6", udf7="v7", udf8="v8", udf9="v9", udf10="v10",
            udf11="v11", udf12="v12", udf13="v13", udf14="v14", udf15="v15",
        )
        for i in range(1, 16):
            self.assertEqual(getattr(meta, f"udf{i}"), f"v{i}")

    def test_udf6_to_udf15_default_to_none(self):
        meta = MetaInfo(udf1="only_first")
        for i in range(6, 16):
            self.assertIsNone(getattr(meta, f"udf{i}"), f"udf{i} should default to None")

    def test_build_meta_info_with_all_15_fields(self):
        meta = MetaInfo.build_meta_info(
            udf1="v1", udf2="v2", udf3="v3", udf4="v4", udf5="v5",
            udf6="v6", udf7="v7", udf8="v8", udf9="v9", udf10="v10",
            udf11="v11", udf12="v12", udf13="v13", udf14="v14", udf15="v15",
        )
        for i in range(1, 16):
            self.assertEqual(getattr(meta, f"udf{i}"), f"v{i}")

    def test_build_meta_info_only_udf1_required(self):
        meta = MetaInfo.build_meta_info(udf1="required")
        self.assertEqual(meta.udf1, "required")
        for i in range(2, 16):
            self.assertIsNone(getattr(meta, f"udf{i}"), f"udf{i} should default to None")

    def test_meta_info_serializes_udf6_to_udf15(self):
        meta = MetaInfo.build_meta_info(udf1="a", udf6="six", udf15="fifteen")
        data = meta.to_dict()
        self.assertEqual(data.get("udf6"), "six")
        self.assertEqual(data.get("udf15"), "fifteen")
