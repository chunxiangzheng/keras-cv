# Copyright 2022 The KerasCV Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools

import tensorflow as tf
from absl.testing import parameterized

from keras_cv import bounding_box

xyxy_box = tf.constant([[10, 10, 110, 110], [20, 20, 120, 120]], dtype=tf.float32)
rel_xyxy_box = tf.constant(
    [[0.01, 0.01, 0.11, 0.11], [0.02, 0.02, 0.12, 0.12]], dtype=tf.float32
)
center_xywh_box = tf.constant(
    [[60, 60, 100, 100], [70, 70, 100, 100]], dtype=tf.float32
)
xywh_box = tf.constant([[10, 10, 100, 100], [20, 20, 100, 100]], dtype=tf.float32)

images = tf.ones([2, 1000, 1000, 3])

boxes = {
    "xyxy": xyxy_box,
    "center_xywh": center_xywh_box,
    "xywh": xywh_box,
    "rel_xyxy": rel_xyxy_box,
}

test_cases = [
    (f"{source}_{target}", source, target)
    for (source, target) in itertools.permutations(boxes.keys(), 2)
]


class ConvertersTestCase(tf.test.TestCase, parameterized.TestCase):
    @parameterized.named_parameters(*test_cases)
    def test_converters(self, source, target):
        source_box = boxes[source]
        target_box = boxes[target]

        self.assertAllClose(
            bounding_box.convert_format(
                source_box, source=source, target=target, images=images
            ),
            target_box,
        )
