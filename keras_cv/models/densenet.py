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

"""DenseNet models for KerasCV.

Reference:
  - [Densely Connected Convolutional Networks (CVPR 2017)](https://arxiv.org/abs/1608.06993)
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import backend
from tensorflow.keras import layers

from keras_cv.models import utils

BN_AXIS = 3


def dense_block(x, blocks, name):
    """A dense block.

    Args:
      x: input tensor.
      blocks: integer, the number of building blocks.
      name: string, block label.

    Returns:
      Output tensor for the block.
    """
    for i in range(blocks):
        x = conv_block(x, 32, name=name + "_block" + str(i + 1))
    return x


def transition_block(x, reduction, name):
    """A transition block.

    Args:
      x: input tensor.
      reduction: float, compression rate at transition layers.
      name: string, block label.

    Returns:
      output tensor for the block.
    """
    x = layers.BatchNormalization(axis=BN_AXIS, epsilon=1.001e-5, name=name + "_bn")(x)
    x = layers.Activation("relu", name=name + "_relu")(x)
    x = layers.Conv2D(
        int(backend.int_shape(x)[BN_AXIS] * reduction),
        1,
        use_bias=False,
        name=name + "_conv",
    )(x)
    x = layers.AveragePooling2D(2, strides=2, name=name + "_pool")(x)
    return x


def conv_block(x, growth_rate, name):
    """A building block for a dense block.

    Args:
      x: input tensor.
      growth_rate: float, growth rate at dense layers.
      name: string, block label.

    Returns:
      Output tensor for the block.
    """
    x1 = layers.BatchNormalization(axis=BN_AXIS, epsilon=1.001e-5, name=name + "_0_bn")(
        x
    )
    x1 = layers.Activation("relu", name=name + "_0_relu")(x1)
    x1 = layers.Conv2D(4 * growth_rate, 1, use_bias=False, name=name + "_1_conv")(x1)
    x1 = layers.BatchNormalization(axis=BN_AXIS, epsilon=1.001e-5, name=name + "_1_bn")(
        x1
    )
    x1 = layers.Activation("relu", name=name + "_1_relu")(x1)
    x1 = layers.Conv2D(
        growth_rate, 3, padding="same", use_bias=False, name=name + "_2_conv"
    )(x1)
    x = layers.Concatenate(axis=BN_AXIS, name=name + "_concat")([x, x1])
    return x

def _get_name(blocks):
    if blocks == [6, 12, 24, 16]:
        return "densenet121"
    if blocks == [6, 12, 32, 32]:
        return "densenet169"
    if blocks == [6, 12, 48, 32]:
        return "densenet201"
    return "densenet"

def _apply_classifier(x, classes, classifier_activation):
    x = layers.GlobalAveragePooling2D(name="avg_pool")(x)
    x = layers.Dense(classes, activation=classifier_activation, name="predictions")(x)
    return x

def _apply_pooling_layer(x, pooling):
    print(x.shape)
    if pooling == "avg":
        return layers.GlobalAveragePooling2D(name="avg_pool")(x)
    if pooling == "max":
        return layers.GlobalMaxPooling2D(name="max_pool")(x)
    return x


def DenseNet(
    blocks,
    include_preprocessing,
    include_top=True,
    weights=None,
    input_tensor=None,
    input_shape=(None, None, 3),
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
):
    """Instantiates the DenseNet architecture.

    Reference:
    - [Densely Connected Convolutional Networks (CVPR 2017)](
        https://arxiv.org/abs/1608.06993)

    This function returns a Keras DenseNet model.

    For transfer learning use cases, make sure to read the
    [guide to transfer learning & fine-tuning](
      https://keras.io/guides/transfer_learning/).

    Args:
      blocks: numbers of building blocks for the four dense layers.
      include_preprocessing: whether or not to Rescale the inputs.
        If set to True, inputs will be passed through a
        `Rescaling(1/255.0)` layer.
      include_top: whether to include the fully-connected
        layer at the top of the network.
      weights: one of `None` (random initialization), or a pretrained
        checkpoint.
      input_tensor: optional Keras tensor
        (i.e. output of `layers.Input()`)
        to use as image input for the model.
      input_shape: optional shape tuple, defaults to (None, None, 3).
      pooling: optional pooling mode for feature extraction
        when `include_top` is `False`.
        - `None` means that the output of the model will be
            the 4D tensor output of the
            last convolutional block.
        - `avg` means that global average pooling
            will be applied to the output of the
            last convolutional block, and thus
            the output of the model will be a 2D tensor.
        - `max` means that global max pooling will
            be applied.
      classes: optional number of classes to classify images
        into, only to be specified if `include_top` is True, and
        if no `weights` argument is specified.
      classifier_activation: A `str` or callable. The activation function to use
        on the "top" layer. Ignored unless `include_top=True`. Set
        `classifier_activation=None` to return the logits of the "top" layer.
        When loading pretrained weights, `classifier_activation` can only
        be `None` or `"softmax"`.

    Returns:
      A `keras.Model` instance.
    """
    if not (weights in {None} or tf.io.gfile.exists(weights)):
        raise ValueError(
            "The `weights` argument should be either "
            "`None` or the path to the weights file to be loaded."
        )

    if include_top and None in input_shape:
        raise ValueError(
            "If `include_top` is True, "
            "you should specify a static `input_shape`. "
            f"Received: input_shape={input_shape}"
        )

    # Determine proper input shape
    img_input = utils.get_input_tensor(input_shape, input_tensor)

    if include_preprocessing:
        x = layers.Rescaling(1 / 255.0)

    x = layers.ZeroPadding2D(padding=((3, 3), (3, 3)))(img_input)
    x = layers.Conv2D(64, 7, strides=2, use_bias=False, name="conv1/conv")(x)
    x = layers.BatchNormalization(axis=BN_AXIS, epsilon=1.001e-5, name="conv1/bn")(x)
    x = layers.Activation("relu", name="conv1/relu")(x)
    x = layers.ZeroPadding2D(padding=((1, 1), (1, 1)))(x)
    x = layers.MaxPooling2D(3, strides=2, name="pool1")(x)

    x = dense_block(x, blocks[0], name="conv2")
    x = transition_block(x, 0.5, name="pool2")
    x = dense_block(x, blocks[1], name="conv3")
    x = transition_block(x, 0.5, name="pool3")
    x = dense_block(x, blocks[2], name="conv4")
    x = transition_block(x, 0.5, name="pool4")
    x = dense_block(x, blocks[3], name="conv5")

    x = layers.BatchNormalization(axis=BN_AXIS, epsilon=1.001e-5, name="bn")(x)
    x = layers.Activation("relu", name="relu")(x)

    if include_top:
        x = _apply_classifier(x, classes, classifier_activation)
    else:
        x = _apply_pooling_layer(x, pooling)

    if input_tensor is not None:
        inputs = keras.utils.get_source_inputs(input_tensor)
    else:
        inputs = img_input

    model = keras.Model(inputs, x, name=_get_name(blocks))

    if weights is not None:
        model.load_weights(weights)
    return model


def DenseNet121(
    include_preprocessing,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=(None, None, 3),
    pooling=None,
    classes=1000,
    **kwargs,
):
    return DenseNet(
        [6, 12, 24, 16],
        include_preprocessing,
        include_top,
        weights,
        input_tensor,
        input_shape,
        pooling,
        classes,
        **kwargs,
    )


def DenseNet169(
    include_preprocessing,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=(None, None, 3),
    pooling=None,
    classes=1000,
    **kwargs,
):
    return DenseNet(
        [6, 12, 32, 32],
        include_preprocessing,
        include_top,
        weights,
        input_tensor,
        input_shape,
        pooling,
        classes,
        **kwargs,
    )


def DenseNet201(
    include_preprocessing,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=(None, None, 3),
    pooling=None,
    classes=1000,
    **kwargs,
):
    return DenseNet(
        [6, 12, 48, 32],
        include_preprocessing,
        include_top,
        weights,
        input_tensor,
        input_shape,
        pooling,
        classes,
        **kwargs,
    )


setattr(DenseNet121, "__doc__", DenseNet.__doc__)
setattr(DenseNet169, "__doc__", DenseNet.__doc__)
setattr(DenseNet201, "__doc__", DenseNet.__doc__)