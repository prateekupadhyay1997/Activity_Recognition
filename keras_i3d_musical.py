# -*- coding: utf-8 -*-
"""Keras_i3d_musical.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1F-Mzw8PBm5xl6lieBtemNT-3XLh8mXM6

# Version_Control
"""

!pip install tensorflow==2.4.1
!pip install tensorflow-gpu==2.4.1
!pip install keras==2.5.0rc0
!pip uninstall keras
!pip install keras==2.4.3

import warnings
import os
import pandas as pd
import cv2
import numpy as np
from keras.layers import Input
from keras.models import Model
from keras.models import Sequential
from keras import layers
from keras.layers import Flatten
from keras.layers import Activation
from keras.layers import Dense
from keras.layers import Input
from keras.layers import BatchNormalization
from keras.layers import Conv3D
from keras.layers import MaxPooling3D
from keras.layers import AveragePooling3D
from keras.layers import Dropout
from keras.layers import Reshape
from keras.layers import Lambda
from keras.layers import GlobalAveragePooling3D
from keras.engine.topology import get_source_inputs
from keras.utils import layer_utils
from keras.utils.data_utils import get_file
from keras.utils import np_utils
from keras import backend as K

from sklearn.utils import shuffle
from collections import deque
from collections import Counter
import copy
import matplotlib
import matplotlib.pyplot as plt
from natsort import natsorted,ns

"""# Video to frames generator

"""

from google.colab import drive
drive.mount('/content/drive')

root_dir = '//'
dest_dir = '//'

if not os.path.exists(dest_dir):
    os.mkdir(dest_dir)

# To list what are the directories - train, test
data_dir_list = os.listdir(root_dir)

def vid_to_frames():
    for data_dir in data_dir_list: # read the train and test directory one by one
        data_path = os.path.join(root_dir,data_dir) # 'UCF-101/train'
        dest_data_path = os.path.join(dest_dir,data_dir) # 'activity_data/train'
        if not os.path.exists(dest_data_path):
            os.mkdir(dest_data_path)
        
        activity_list = os.listdir(data_path) # thre activity directories ['Archery', 'Basketball', 'Biking']
        
        for activity in activity_list: # loop over every activity folder
            activity_path = os.path.join(data_path,activity) # 'UCF-101/train/Archery'
            dest_activity_path = os.path.join(dest_data_path,activity) # 'activity_data/train/Archery'
            if not os.path.exists(dest_activity_path):
                os.mkdir(dest_activity_path)
            write_frames(activity_path,dest_activity_path)
    
def write_frames(activity_path,dest_activity_path):
    # read the list of video from 'UCF-101/train/Archery' - [v_Archery_g01_c01.avi,v_Archery_g01_c01.avi, ......]
    vid_list = os.listdir(activity_path) 
    for vid in vid_list: # v_Archery_g01_c01.avi
        dest_folder_name = vid[:-4] # v_Archery_g01_c01
        dest_folder_path = os.path.join(dest_activity_path,dest_folder_name) # 'activity_data/train/Archery/v_Archery_g01_c01'
        if os.path.exists(dest_folder_path):
        	print("Already Exists")
        	continue
        else:
        	os.mkdir(dest_folder_path)
            
        vid_path = os.path.join(activity_path,vid)  # 'UCF-101/train/Archery/v_Archery_g01_c01.avi'
        print ('video path: ', vid_path)
        cap = cv2.VideoCapture(vid_path) # initialize a cap object for reading the video
        
        ret=True
        frame_num=0
        while ret:
            ret, img = cap.read()
            
            output_file_name = 'img_{:06d}'.format(frame_num) + '.jpg' # img_000001.png
            # output frame to write 'activity_data/train/Archery/v_Archery_g01_c01/img_000001.png'
            output_file_path = os.path.join(dest_folder_path, output_file_name)
            frame_num += 1
            print("Frame no. ", frame_num)
            try:
                #cv2.imshow('img',img)
                cv2.waitKey(5)
                img_r = cv2.resize(img,(224,224))
                cv2.imwrite(output_file_path, img_r) # writing frames to defined location
            except Exception as e:
                print(e)
            if ret==False:
                cv2.destroyAllWindows()
                cap.release()
if __name__ == '__main__':
    vid_to_frames()

"""#Creating CSV Files of Videos Per Action"""

num_classes = 10
action_dict = {0:'Drumming',1: 'PlayingCello',2: 'PlayingDaf',3: 'PlayingDhol',4: 'PlayingFlute',5: 'PlayingGuitar',6: 'PlayingPiano',7: 'PlayingSitar',8: 'PlayingTabla',9: 'PlayingViolin'}
labels_name = {'Drumming':0, 'PlayingCello':1, 'PlayingDaf':2, 'PlayingDhol':3, 'PlayingFlute':4, 'PlayingGuitar':5, 'PlayingPiano':6, 'PlayingSitar':7, 'PlayingTabla':8, 'PlayingViolin':9}  
train_data_path = os.path.join('/content/drive/MyDrive/activity_recognition/activity_data/','train')
val_data_path = os.path.join('/content/drive/MyDrive/activity_data/activity_recognition/','val')

if not os.path.exists('/content/drive/MyDrive/activity_recognition/activity_data/data_files'):
    os.mkdir('/content/drive/MyDrive/activity_recognition/activity_data/data_files')
if not os.path.exists('/content/drive/MyDrive/activity_recognition/activity_data/data_files/train'):
    os.mkdir('/content/drive/MyDrive/activity_recognition/activity_data/data_files/train') 
if not os.path.exists('/content/drive/MyDrive/activity_recognition/activity_data/data_files'):
    os.mkdir('/content/drive/MyDrive/activity_recognition/activity_data/data_files')
if not os.path.exists('/content/drive/MyDrive/activity_recognition/activity_data/data_files/val'):
    os.mkdir('/content/drive/MyDrive/activity_recognition/activity_data/data_files/val')
    
    
data_dir_list = os.listdir(train_data_path)
print(data_dir_list)

## train dataset
data_dir_list = os.listdir(train_data_path)
for data_dir in data_dir_list: 
    label = labels_name[str(data_dir)]
    video_list = os.listdir(os.path.join(train_data_path,data_dir))
    for vid in video_list: 
        train_df = pd.DataFrame(columns=['FileName', 'Label', 'ClassName'])
        img_list = os.listdir(os.path.join(train_data_path,data_dir,vid))
        img_list = natsorted(img_list,key=lambda y:y.lower())
        for img in img_list:
            img_path = os.path.join(train_data_path,data_dir,vid,img)
            train_df = train_df.append({'FileName': img_path, 'Label': label,'ClassName':data_dir },ignore_index=True)
        file_name='{}_{}.csv'.format(data_dir,vid)
        train_df.to_csv('/content/drive/MyDrive/activity_recognition/activity_data/data_files/train/{}'.format(file_name))

# val dataset



val_data_dir_list = os.listdir(val_data_path)
for val_data_dir in val_data_dir_list: 
    label = labels_name[str(val_data_dir)]
    video_list = os.listdir(os.path.join(val_data_path,val_data_dir))
    for vid in video_list: 
        val_df = pd.DataFrame(columns=['FileName', 'Label', 'ClassName'])
        img_list = os.listdir(os.path.join(val_data_path,val_data_dir,vid))
        img_list = natsorted(img_list,key=lambda y:y.lower())
        for img in img_list:
            img_path = os.path.join(val_data_path,val_data_dir,vid,img)
            val_df = val_df.append({'FileName': img_path, 'Label': label,'ClassName':val_data_dir},ignore_index=True)
        file_name='{}_{}.csv'.format(val_data_dir,vid)
        val_df.to_csv('/content/drive/MyDrive/activity_recognition/activity_data/data_files/val/{}'.format(file_name))

"""# Keras Custom Generator"""

class Config():
    def __init__(self):
        pass
    
    num_classes = 10
    labels_to_class = {0: 'Drumming',1: 'PlayingCello',2: 'PlayingDaf',3: 'PlayingDhol',4: 'PlayingFlute',5: 'PlayingGuitar',6: 'PlayingPiano',7: 'PlayingSitar',8: 'PlayingTabla',9: 'PlayingViolin'}
    class_to_labels = {'Drumming':0, 'PlayingCello':1, 'PlayingDaf':2, 'PlayingDhol':3, 'PlayingFlute':4, 'PlayingGuitar':5, 'PlayingPiano':6, 'PlayingSitar':7, 'PlayingTabla':8, 'PlayingViolin':9}
    resize = 224
    num_epochs = 100
    batch_size = 16

#!/usr/bin/env python
# coding: utf-8

class KerasCustomGenerator(object):
    
    def __init__(self,root_data_path,temporal_stride=1,temporal_length=16,resize=224):
        
        self.root_data_path = root_data_path
        self.temporal_length = temporal_length
        self.temporal_stride = temporal_stride
        self.resize=resize
    def file_generator(self,data_path,data_files):
        '''
        data_files - list of csv files to be read.
        '''
        for f in data_files:       
            tmp_df = pd.read_csv(os.path.join(data_path,f))
            label_list = list(tmp_df['Label'])
            total_images = len(label_list) 
            if total_images>=self.temporal_length:
                num_samples = int((total_images-self.temporal_length)/self.temporal_stride)+1
                print ('num of samples from vid seq-{}: {}'.format(f,num_samples))
                img_list = list(tmp_df['FileName'])
            else:
                print ('num of frames is less than temporal length; hence discarding this file-{}'.format(f))
                continue
            
            start_frame = 0
            samples = deque()
            samp_count=0
            for img in img_list:
                samples.append(img)
                if len(samples)==self.temporal_length:
                    samples_c=copy.deepcopy(samples)
                    samp_count+=1
                    for t in range(self.temporal_stride):
                        samples.popleft() 
                    yield samples_c,label_list[0]

    def load_samples(self,data_cat='val'):
        data_path = os.path.join(self.root_data_path,data_cat)
        csv_data_files = os.listdir(data_path)
        file_gen = self.file_generator(data_path,csv_data_files)
        iterator = True
        data_list = []
        while iterator:
            try:
                x,y = next(file_gen)
                x=list(x)
                data_list.append([x,y])
            except Exception as e:
                print ('the exception: ',e)
                iterator = False
                print ('end of data generator')
        return data_list
    
    def shuffle_data(self,samples):
        data = shuffle(samples,random_state=2)
        return data
    
    def preprocess_image(self,img):
        img = cv2.resize(img,(self.resize,self.resize))
        img = img/255.0
        return img
    
    def data_generator(self,data,batch_size=4,shuffle=True):              
        """
        Yields the next training batch.
        data is an array [[img1_filename,img2_filename...,img16_filename],label1], [image2_filename,label2],...].
        """
        num_samples = len(data)
        if shuffle:
            data = self.shuffle_data(data)
        while True:   
            for offset in range(0, num_samples, batch_size):
                batch_samples = data[offset:offset+batch_size]
               
                X_train = []
                y_train = []
               
                for batch_sample in batch_samples:
                    x = batch_sample[0]
                    y = batch_sample[1]
                    temp_data_list = []
                    for img in x:
                        try:
                            img = cv2.imread(img)
                            #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
                            img = self.preprocess_image(img)
                            temp_data_list.append(img)
    
                        except Exception as e:
                            print (e)
                            print ('error reading file: ',img)  
    
                    X_train.append(temp_data_list)
                    y_train.append(y)
        
                
                X_train = np.array(X_train)
              
                y_train = np.array(y_train)
               
                y_train = np_utils.to_categorical(y_train, 21)           
                yield X_train, y_train

root_data_path='/content/drive/MyDrive/activity_recognition/activity_data/data_files'
DataGenerator=KerasCustomGenerator(root_data_path,temporal_stride=12,temporal_length=12,resize=224)

train_data = DataGenerator.load_samples(data_cat='train')
test_data = DataGenerator.load_samples(data_cat='val')

print('num of train_samples: {}'.format(len(train_data)))
print('num of test_samples: {}'.format(len(test_data)))

train_generator = DataGenerator.data_generator(train_data,batch_size=16,shuffle=True)
test_generator = DataGenerator.data_generator(test_data,batch_size=16,shuffle=True)

"""# Model Architecture"""

def conv3d_bn(x,
              filters,
              num_frames,
              num_row,
              num_col,
              padding='same',
              strides=(1, 1, 1),
              use_bias = False,
              use_activation_fn = True,
              use_bn = True,
              name=None):
    """Utility function to apply conv3d + BN.
    # Arguments
        x: input tensor.
        filters: filters in `Conv3D`.
        num_frames: frames (time depth) of the convolution kernel.
        num_row: height of the convolution kernel.
        num_col: width of the convolution kernel.
        padding: padding mode in `Conv3D`.
        strides: strides in `Conv3D`.
        use_bias: use bias or not  
        use_activation_fn: use an activation function or not.
        use_bn: use batch normalization or not.
        name: name of the ops; will become `name + '_conv'`
            for the convolution and `name + '_bn'` for the
            batch norm layer.
    # Returns
        Output tensor after applying `Conv3D` and `BatchNormalization`.
    """
    if name is not None:
        bn_name = name + '_bn'
        conv_name = name + '_conv'
    else:
        bn_name = None
        conv_name = None

    x = Conv3D(
        filters, (num_frames, num_row, num_col),
        strides=strides,
        padding=padding,
        use_bias=use_bias,
        name=conv_name)(x)

    if use_bn:
        bn_axis = 4
        x = BatchNormalization(axis=bn_axis, scale=False, name=bn_name)(x)

    if use_activation_fn:
        x = Activation('relu', name=name)(x)

    return x

def Inception_Inflated3d(classes=20,input_tensor=None,input_shape=None):
    """Instantiates the Inflated 3D Inception v1 architecture.
    Optionally loads weights pre-trained
    on Kinetics. Note that when using TensorFlow,
    for best performance you should set
    `image_data_format='channels_last'` in your Keras config
    at ~/.keras/keras.json.
    The model and the weights are compatible with both
    TensorFlow and Theano. The data format
    convention used by the model is the one
    specified in your Keras config file.
    Note that the default input frame(image) size for this model is 224x224.
    # Arguments
        include_top: whether to include the the classification 
            layer at the top of the network.
        weights: one of `None` (random initialization)
            or 'kinetics_only' (pre-training on Kinetics dataset only).
            or 'imagenet_and_kinetics' (pre-training on ImageNet and Kinetics datasets).
        input_tensor: optional Keras tensor (i.e. output of `layers.Input()`)
            to use as image input for the model.
        input_shape: optional shape tuple, only to be specified
            if `include_top` is False (otherwise the input shape
            has to be `(NUM_FRAMES, 224, 224, 3)` (with `channels_last` data format)
            or `(NUM_FRAMES, 3, 224, 224)` (with `channels_first` data format).
            It should have exactly 3 inputs channels.
            NUM_FRAMES should be no smaller than 8. The authors used 64
            frames per example for training and testing on kinetics dataset
            Also, Width and height should be no smaller than 32.
            E.g. `(64, 150, 150, 3)` would be one valid value.
        dropout_prob: optional, dropout probability applied in dropout layer
            after global average pooling layer. 
            0.0 means no dropout is applied, 1.0 means dropout is applied to all features.
            Note: Since Dropout is applied just before the classification
            layer, it is only useful when `include_top` is set to True.
        endpoint_logit: (boolean) optional. If True, the model's forward pass
            will end at producing logits. Otherwise, softmax is applied after producing
            the logits to produce the class probabilities prediction. Setting this parameter 
            to True is particularly useful when you want to combine results of rgb model
            and optical flow model.
            - `True` end model forward pass at logit output
            - `False` go further after logit to produce softmax predictions
            Note: This parameter is only useful when `include_top` is set to True.
        classes: optional number of classes to classify images
            into, only to be specified if `include_top` is True, and
            if no `weights` argument is specified.
    # Returns
        A Keras model instance.
    # Raises
        ValueError: in case of invalid argument for `weights`,
            or invalid input shape.
    """

    channel_axis = 4
    img_input = Input(shape=input_shape)

    # Downsampling via convolution (spatial and temporal)
    x = conv3d_bn(img_input, 64, 7, 7, 7, strides=(2, 2, 2), padding='same', name='Conv3d_1a_7x7')

    # Downsampling (spatial only)
    x = MaxPooling3D((1, 3, 3), strides=(1, 2, 2), padding='same', name='MaxPool2d_2a_3x3')(x)
    x = conv3d_bn(x, 64, 1, 1, 1, strides=(1, 1, 1), padding='same', name='Conv3d_2b_1x1')
    x = conv3d_bn(x, 192, 3, 3, 3, strides=(1, 1, 1), padding='same', name='Conv3d_2c_3x3')

    # Downsampling (spatial only)
    x = MaxPooling3D((1, 3, 3), strides=(1, 2, 2), padding='same', name='MaxPool2d_3a_3x3')(x)

    # Mixed 3b
    branch_0 = conv3d_bn(x, 64, 1, 1, 1, padding='same', name='Conv3d_3b_0a_1x1')

    branch_1 = conv3d_bn(x, 96, 1, 1, 1, padding='same', name='Conv3d_3b_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 128, 3, 3, 3, padding='same', name='Conv3d_3b_1b_3x3')

    branch_2 = conv3d_bn(x, 16, 1, 1, 1, padding='same', name='Conv3d_3b_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 32, 3, 3, 3, padding='same', name='Conv3d_3b_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_3b_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 32, 1, 1, 1, padding='same', name='Conv3d_3b_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_3b')

    # Mixed 3c
    branch_0 = conv3d_bn(x, 128, 1, 1, 1, padding='same', name='Conv3d_3c_0a_1x1')

    branch_1 = conv3d_bn(x, 128, 1, 1, 1, padding='same', name='Conv3d_3c_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 192, 3, 3, 3, padding='same', name='Conv3d_3c_1b_3x3')

    branch_2 = conv3d_bn(x, 32, 1, 1, 1, padding='same', name='Conv3d_3c_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 96, 3, 3, 3, padding='same', name='Conv3d_3c_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_3c_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 64, 1, 1, 1, padding='same', name='Conv3d_3c_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_3c')


    # Downsampling (spatial and temporal)
    x = MaxPooling3D((3, 3, 3), strides=(2, 2, 2), padding='same', name='MaxPool2d_4a_3x3')(x)

    # Mixed 4b
    branch_0 = conv3d_bn(x, 192, 1, 1, 1, padding='same', name='Conv3d_4b_0a_1x1')

    branch_1 = conv3d_bn(x, 96, 1, 1, 1, padding='same', name='Conv3d_4b_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 208, 3, 3, 3, padding='same', name='Conv3d_4b_1b_3x3')

    branch_2 = conv3d_bn(x, 16, 1, 1, 1, padding='same', name='Conv3d_4b_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 48, 3, 3, 3, padding='same', name='Conv3d_4b_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_4b_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 64, 1, 1, 1, padding='same', name='Conv3d_4b_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_4b')

    # Mixed 4c
    branch_0 = conv3d_bn(x, 160, 1, 1, 1, padding='same', name='Conv3d_4c_0a_1x1')

    branch_1 = conv3d_bn(x, 112, 1, 1, 1, padding='same', name='Conv3d_4c_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 224, 3, 3, 3, padding='same', name='Conv3d_4c_1b_3x3')

    branch_2 = conv3d_bn(x, 24, 1, 1, 1, padding='same', name='Conv3d_4c_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 64, 3, 3, 3, padding='same', name='Conv3d_4c_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_4c_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 64, 1, 1, 1, padding='same', name='Conv3d_4c_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_4c')

    # Mixed 4d
    branch_0 = conv3d_bn(x, 128, 1, 1, 1, padding='same', name='Conv3d_4d_0a_1x1')

    branch_1 = conv3d_bn(x, 128, 1, 1, 1, padding='same', name='Conv3d_4d_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 256, 3, 3, 3, padding='same', name='Conv3d_4d_1b_3x3')

    branch_2 = conv3d_bn(x, 24, 1, 1, 1, padding='same', name='Conv3d_4d_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 64, 3, 3, 3, padding='same', name='Conv3d_4d_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_4d_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 64, 1, 1, 1, padding='same', name='Conv3d_4d_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_4d')

    # Mixed 4e
    branch_0 = conv3d_bn(x, 112, 1, 1, 1, padding='same', name='Conv3d_4e_0a_1x1')

    branch_1 = conv3d_bn(x, 144, 1, 1, 1, padding='same', name='Conv3d_4e_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 288, 3, 3, 3, padding='same', name='Conv3d_4e_1b_3x3')

    branch_2 = conv3d_bn(x, 32, 1, 1, 1, padding='same', name='Conv3d_4e_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 64, 3, 3, 3, padding='same', name='Conv3d_4e_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_4e_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 64, 1, 1, 1, padding='same', name='Conv3d_4e_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_4e')

    # Mixed 4f
    branch_0 = conv3d_bn(x, 256, 1, 1, 1, padding='same', name='Conv3d_4f_0a_1x1')

    branch_1 = conv3d_bn(x, 160, 1, 1, 1, padding='same', name='Conv3d_4f_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 320, 3, 3, 3, padding='same', name='Conv3d_4f_1b_3x3')

    branch_2 = conv3d_bn(x, 32, 1, 1, 1, padding='same', name='Conv3d_4f_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 128, 3, 3, 3, padding='same', name='Conv3d_4f_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_4f_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 128, 1, 1, 1, padding='same', name='Conv3d_4f_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_4f')


    # Downsampling (spatial and temporal)
    x = MaxPooling3D((2, 2, 2), strides=(2, 2, 2), padding='same', name='MaxPool2d_5a_2x2')(x)

    # Mixed 5b
    branch_0 = conv3d_bn(x, 256, 1, 1, 1, padding='same', name='Conv3d_5b_0a_1x1')

    branch_1 = conv3d_bn(x, 160, 1, 1, 1, padding='same', name='Conv3d_5b_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 320, 3, 3, 3, padding='same', name='Conv3d_5b_1b_3x3')

    branch_2 = conv3d_bn(x, 32, 1, 1, 1, padding='same', name='Conv3d_5b_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 128, 3, 3, 3, padding='same', name='Conv3d_5b_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_5b_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 128, 1, 1, 1, padding='same', name='Conv3d_5b_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_5b')

    # Mixed 5c
    branch_0 = conv3d_bn(x, 384, 1, 1, 1, padding='same', name='Conv3d_5c_0a_1x1')

    branch_1 = conv3d_bn(x, 192, 1, 1, 1, padding='same', name='Conv3d_5c_1a_1x1')
    branch_1 = conv3d_bn(branch_1, 384, 3, 3, 3, padding='same', name='Conv3d_5c_1b_3x3')

    branch_2 = conv3d_bn(x, 48, 1, 1, 1, padding='same', name='Conv3d_5c_2a_1x1')
    branch_2 = conv3d_bn(branch_2, 128, 3, 3, 3, padding='same', name='Conv3d_5c_2b_3x3')

    branch_3 = MaxPooling3D((3, 3, 3), strides=(1, 1, 1), padding='same', name='MaxPool2d_5c_3a_3x3')(x)
    branch_3 = conv3d_bn(branch_3, 128, 1, 1, 1, padding='same', name='Conv3d_5c_3b_1x1')

    x = layers.concatenate(
        [branch_0, branch_1, branch_2, branch_3],
        axis=channel_axis,
        name='Mixed_5c')

    h = int(x.shape[2])
    w = int(x.shape[3])
    x = AveragePooling3D((2, h, w), strides=(1, 1, 1), padding='valid', name='global_avg_pool')(x)



    inputs = img_input
    # create model
    model = Model(inputs, x, name='i3d_inception')
    
    print('Model loaded.')
    # load pretrained_weights
    model.load_weights('/content/drive/MyDrive/activity_recognition/pretrained_weights/rgb_inception_i3d_imagenet_and_kinetics_tf_dim_ordering_tf_kernels_no_top.h5')
    return model



INSHAPE=(NBFRAME,SIZE[0],SIZE[1],CHANNELS) # (64, 224, 224, 3)
print(INSHAPE)
baseModel = Inception_Inflated3d(len(classes),input_tensor=None,input_shape=INSHAPE)
headModel = baseModel.output
headModel = Flatten(name="flatten")(headModel)
headModel = Dense(512, activation="relu")(headModel)
headModel = Dropout(0.5)(headModel)
headModel = Dense(len(classes), activation="softmax")(headModel)
model = Model(inputs=baseModel.input, outputs=headModel)

model.summary()

for layer in model.layers[:153]:
    layer.trainable=False
for i,layer in enumerate(model.layers):
    print(i,layer.name,layer.trainable)

"""# Model Training"""

optimizer = keras.optimizers.Adam(0.0001)
model.compile(
    loss = 'categorical_crossentropy',
    optimizer = optimizer,
    metrics=['accuracy']
)

import math
train_size = 1000
val_size  = 362
BATCH_SIZE = 4
compute_steps_per_epoch = lambda x: int(math.ceil(1. * x / BATCH_SIZE))
steps_per_epoch = compute_steps_per_epoch(train_size)
val_steps = compute_steps_per_epoch(val_size)

EPOCHS=100
# create a "chkp" directory before to run that
# because ModelCheckpoint will write models inside
callbacks = [
    keras.callbacks.ReduceLROnPlateau(verbose=1),
    keras.callbacks.ModelCheckpoint(
        '/content/drive/MyDrive/activity_recognition/weights_musical/_musical.{epoch:02d}-{val_loss:.2f}.hdf5',
        save_freq = 'epoch',
        period = 10,
        verbose=1),
]
history=model.fit(
    train,
    validation_data=valid,
    verbose=1,
    epochs=EPOCHS,
    callbacks=callbacks
)

# list all data in history
print(history.keys())
# summarize history for accuracy
plt.plot(history.history['categorical_accuracy'])
plt.plot(history.history['val_categorical_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

save_path = "/content/drive/MyDrive/activity_recognition/weights_musical/"
model_json = model.to_json()
with open(os.path.join(save_path,"musical_detection.json"),"w") as json_file:
    json_file.write(model_json)

"""# Inference Code"""

PATH_VIDEOS = '/content/drive/MyDrive/activity_recognition/testing/input/'
PATH_OUTPUT = '/content/drive/MyDrive/activity_recognition/testing/output/'

import tensorflow as tf
import tensorflow.keras as keras
from keras.models import model_from_json


with open(os.path.join('/content/drive/MyDrive/activity_recognition/weights_musical', 'musical_detection.json'), 'r') as fp:
    exercise_model_json = fp.read()
musical_model = model_from_json(exercise_model_json)

musical_model.load_weights('/content/drive/MyDrive/activity_recognition/weights_musical/musical.50-0.05.hdf5')

def crop_center_square(frame):
  y, x = frame.shape[0:2]
  min_dim = min(y, x)
  start_x = (x // 2) - (min_dim // 2)
  start_y = (y // 2) - (min_dim // 2)
  return frame[start_y:start_y+min_dim,start_x:start_x+min_dim]

def testing(video_name,path_video=PATH_VIDEOS,path_out=PATH_OUTPUT,label=folder):
  images = []
  input_file = os.path.join(path_video, video_name )
  cap = cv2.VideoCapture(input_file)
  fourcc = cv2.VideoWriter_fourcc(*'mp4v')
  output_file = os.path.join(path_out, video_name )
  out = cv2.VideoWriter(output_file,fourcc, 8.0,(int(cap.get(3)),int(cap.get(4))))

  ret, frame = cap.read()
  frame = crop_center_square(frame1)
 
  counter = 0

  output = 'fetching results..'
  prev_pred=10
  c = 0
  Q = deque(maxlen=5)
  no_move_counter = 0
  while (cap.isOpened()): 
    counter = counter + 1
    
    if counter % 17 == 0 :
      c+=1
      images_NP = np.array(images)
      images_NP = np.expand_dims(images_NP, axis=0)
      #print(images.shape)
      musical_dict = {0: 'Drumming',1: 'PlayingCello',2: 'PlayingDaf',3: 'PlayingDhol',4: 'PlayingFlute',5: 'PlayingGuitar',6: 'PlayingPiano',7: 'PlayingSitar',8: 'PlayingTabla',9: 'PlayingViolin',10: 'None'}

      prediction = model.predict((images_NP/255.0))
      print("label__",str(c))
      print(np.round(prediction,2))
      if (np.any(prediction>=0.85)):
        pred = np.argmax(np.round(prediction,2))
        prev_pred=pred
      #print(prediction)
      else:
        pred = 10

       
      #print("label__"+str(c)+" = "+str(pred))
      #Rolling_average
      Q.append(pred)
      occurence_count = Counter(Q)
      pred = occurence_count.most_common(1)[0][0]
      output = musical_dict[pred]
      test_labels.append(label)
      test_pred.append(output)
      app_output = {'label':output}
      print(app_output)
        
      images = []
    
    else:
      # Capture frame-by-frame 
      ret, frame = cap.read()
      if not(ret): break 
      result = frame.copy()
      frame = crop_center_square(frame)
      frame = cv2.resize(frame, (224, 224))
      images.append(frame)
      result = cv2.putText(result, output, (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
      out.write(result)
      
    # define q as the exit button 
    if cv2.waitKey(25) & 0xFF == ord('q'): 
      break
            
  print("Video Generated")  
  cap.release() 
  images = np.array(images)
  # Closes all the windows currently opened. 
  cv2.destroyAllWindows()



import os.path
for folder in os.listdir(PATH_VIDEOS): 
    #print(os.path.join(PATH_VIDEOS,folder,file))
    for file in os.listdir(os.path.join(PATH_VIDEOS,folder)):
        if os.path.isfile(os.path.join(PATH_VIDEOS,folder,file)):
            print("Read file:", file)
            testing(file, path_video=os.path.join(PATH_VIDEOS,folder), path_out=PATH_OUTPUT,label=folder)
            print("Create video %s successfull" % file)