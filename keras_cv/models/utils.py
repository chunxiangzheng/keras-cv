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

from tensorflow.keras import backend
from tensorflow.keras import layers


def get_input_tensor(input_shape, input_tensor):
    if input_tensor is None:
        return layers.Input(shape=input_shape)
    if not backend.is_keras_tensor(input_tensor):
        return layers.Input(tensor=input_tensor, shape=input_shape)
    return input_tensor
