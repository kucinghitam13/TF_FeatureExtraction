# MIT License
#
# Copyright (c) 2017 Tom Runia
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to conditions.
#
# Author: Tom Runia
# Date Created: 2017-08-15

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import utils
import numpy as np
from scipy import misc
from feature_extractor import FeatureExtractor


def classification_queue_input(feature_extractor, image_path, layer_names,
                               batch_size, num_classes):
    '''
    Example function for performing image classification using a pre-trained
    network. This tests the filename queue as input method. Given a list of
    image files to process, these are fed into the filename queue and then the
    images are dequeued from the queue and classified.


    :param feature_extractor: object, TF feature extractor
    :param image_path: str, path to directory containing images
    :param layer_names: list of str, list of layer names (should refer to `logits`)
    :param batch_size: int, batch size
    :param num_classes: int, number of classes for ImageNet (1000 or 1001)
    :return:
    '''

    # Add a list of images to process
    image_files = utils.find_files(image_path, ("jpg", "png"))

    # Push the images through the network
    feature_extractor.enqueue_image_files(image_files)
    outputs = feature_extractor.feed_forward_batch(layer_names, fetch_images=True)

    # Compute the predictions, note that we asume layer_names[0] corresponds to logits
    predictions = np.squeeze(outputs[0])
    predictions = np.argmax(predictions, axis=1)

    for i in range(batch_size):
        image = misc.imread(image_files[i])
        class_index = predictions[i] if num_classes == 1001 else predictions[i]+1
        utils.display_imagenet_prediction(image, class_index)


def classification_placeholder_input(feature_extractor, image_path, layer_names,
                                     batch_size, num_classes):
    '''
    Example function for performing image classification using a pre-trained
    network. This function test simple the simple input method using placeholders.
    It loads one batch of images from disk, pre-processes them using Inception
    pre-processing and then feed-forwards them through the network. Input images
    and predicted ImageNet classes are displayed once finished.

    :param feature_extractor: object, TF feature extractor
    :param image_path: str, path to directory containing images
    :param layer_names: list of str, list of layer names (should refer to `logits`)
    :param batch_size: int, batch size
    :param num_classes: int, number of classes for ImageNet (1000 or 1001)
    :return:
    '''

    # Add a list of images to process
    image_files = utils.find_files(image_path, ("jpg", "png"))

    # Load one batch of images
    batch_images = np.zeros([batch_size, feature_extractor.image_size,
                             feature_extractor.image_size, 3], dtype=np.float32)

    for i in range(batch_size):
        # Note: this corresponds to 'inception' preprocessing. You don't need
        # this when using the queues as input pipeline, since the get_preprocessing()
        # function automatically determines it.
        image = misc.imread(image_files[i])
        image = misc.imresize(
            image, (feature_extractor.image_size, feature_extractor.image_size))
        image = (image/255.0).astype(dtype=np.float32)
        image -= 0.5
        image *= 2.0
        batch_images[i] = image

    # Push the images through the network
    outputs = feature_extractor.feed_forward_batch(
        layer_names, batch_images, fetch_images=True)

    # Compute the predictions, note that we asume layer_names[0] corresponds to logits
    predictions = np.squeeze(outputs[0])
    predictions = np.argmax(predictions, axis=1)

    # Display predictions
    for i in range(batch_size):
        image = (((batch_images[i]/2.0)+0.5)*255.0).astype(np.uint8)
        class_index = predictions[i] if num_classes == 1001 else predictions[i]+1
        utils.display_imagenet_prediction(image, class_index)


################################################################################
################################################################################
################################################################################


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="TensorFlow feature extraction")
    parser.add_argument("--network", dest="network_name", type=str, required=True, help="model name, e.g. 'resnet_v2_101'")
    parser.add_argument("--checkpoint", dest="checkpoint", type=str, required=True, help="path to pre-trained checkpoint file")
    parser.add_argument("--image_path", dest="image_path", type=str, required=True, help="path to directory containing images")
    parser.add_argument("--layer_names", dest="layer_names", type=str, required=True, help="layer names separated by commas")
    parser.add_argument("--preproc_func", dest="preproc_func", type=str, default=None, help="force the image preprocessing function (None)")
    parser.add_argument("--batch_size", dest="batch_size", type=int, default=32, help="batch size (32)")
    parser.add_argument("--num_classes", dest="num_classes", type=int, default=1001, help="number of classes (1001)")
    args = parser.parse_args()

    # resnet_v2_101/logits,resnet_v2_101/pool4 => to list of layer names
    layer_names = args.layer_names.split(",")

    # Initialize the feature extractor
    feature_extractor = FeatureExtractor(
        network_name=args.network_name,
        checkpoint_path=args.checkpoint,
        batch_size=args.batch_size,
        num_classes=args.num_classes,
        preproc_func_name=args.preproc_func)

    # Print the network summary, use these layer names for feature extraction
    feature_extractor.print_network_summary()

    # OPTION 1. Test image classification using a filename queue to feed images
    classification_queue_input(feature_extractor, args.image_path,
                               layer_names, args.batch_size, args.num_classes)

    # OPTION 2. Test image classification by manually feeding images into placeholders
    classification_placeholder_input(feature_extractor, args.image_path,
                                     layer_names, args.batch_size, args.num_classes)
