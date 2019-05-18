#https://github.com/geifmany/keras_imagenet_training/blob/master/imagenet.py
from __future__ import print_function
import keras
from keras.preprocessing.image import ImageDataGenerator
from keras import optimizers

#https://stackoverflow.com/questions/43137288/how-to-determine-needed-memory-of-keras-model
def get_model_memory_usage(batch_size, model):
    import numpy as np
    from keras import backend as K

    shapes_mem_count = 0
    for l in model.layers:
        single_layer_mem = 1
        for s in l.output_shape:
            if s is None:
                continue
            single_layer_mem *= s
        shapes_mem_count += single_layer_mem

    trainable_count = np.sum([K.count_params(p) for p in set(model.trainable_weights)])
    non_trainable_count = np.sum([K.count_params(p) for p in set(model.non_trainable_weights)])

    number_size = 4.0
    if K.floatx() == 'float16':
         number_size = 2.0
    if K.floatx() == 'float64':
         number_size = 8.0

    total_memory = number_size*(batch_size*shapes_mem_count + trainable_count + non_trainable_count)
    gbytes = np.round(total_memory / (1024.0 ** 3), 3)
    return gbytes

class imagenet:
    def __init__(self, train_dir = None, val_dir = None,architecture = 'mobilenet'):
        self.num_classes = 200
        self.weight_decay = 0.0005
        self.x_shape = [224,224,3]
        self.train_dir = train_dir
        self.val_dir = val_dir
        if architecture == "mobilenet":
            self.model = keras.applications.mobilenet.MobileNet(weights = None,input_shape=None, alpha=1.0, depth_multiplier=1, dropout=1e-3, include_top=True, input_tensor=None, pooling=None, classes=self.num_classes)
            self.model.summary()
            self.memory_usage = get_model_memory_usage(1,self.model)
            print(self.memory_usage)
            self.batch_size = int(8.0 // self.memory_usage)
            print(self.batch_size)
            # self.batch_size = None
        elif architecture == "resnet50":
            self.model =keras.applications.resnet50.ResNet50(include_top=True, weights=None, input_tensor=None, input_shape=None, pooling=None, classes=self.num_classes)

            # self.batch_size = 64
        self.train(self.model)

    def normalize_production(self,img):

        img[:, :, 0] -= 103.939
        img[:, :, 1] -= 116.779
        img[:, :, 2] -= 123.68
        return img

    def predict(self,x,normalize=True,batch_size=50):
        if normalize:
            x = self.normalize_production(x)
        return self.model.predict(x,batch_size)

    def train(self,model):

        #training parameters
        maxepoches = 100
        learning_rate = 0.1
        lr_decay = 1e-6
        lr_drop = 30
        lr_decay_factor=0.1
        def normalize_production(img):

            img[:, :, 0] -= 103.939
            img[:, :, 1] -= 116.779
            img[:, :, 2] -= 123.68
            return img

        def lr_scheduler(epoch):
            return learning_rate * (lr_decay_factor ** (epoch // lr_drop))
        reduce_lr = keras.callbacks.LearningRateScheduler(lr_scheduler)
        checkpointer = keras.callbacks.ModelCheckpoint(filepath='best_model.h5', verbose=1, save_best_only=True)

        #data augmentation
        datagen = ImageDataGenerator(
            featurewise_center=True,  # set input mean to 0 over the dataset
            samplewise_center=False,  # set each sample mean to 0
            featurewise_std_normalization=False,  # divide inputs by std of the dataset
            samplewise_std_normalization=False,  # divide each input by its std
            zca_whitening=False,  # apply ZCA whitening
            vertical_flip=False,
            preprocessing_function=normalize_production)  # randomly flip images

        #optimization details
        sgd = optimizers.SGD(lr=learning_rate, decay=lr_decay, momentum=0.9, nesterov=True)
        model.compile(loss='categorical_crossentropy', optimizer=sgd,metrics=['accuracy'])

        train_generator = datagen.flow_from_directory(
            self.train_dir,
            target_size=(224, 224),
            batch_size=self.batch_size)

        validation_generator = datagen.flow_from_directory(
            self.val_dir,
            target_size=(224, 224),
            batch_size=self.batch_size)

        history = model.fit_generator(
            train_generator,
            steps_per_epoch=1280924//self.batch_size,
            epochs=maxepoches,
            validation_data=validation_generator,
            validation_steps=50000//self.batch_size,
            callbacks=[checkpointer,reduce_lr])

        return model

if __name__ == '__main__':
    model = imagenet(train_dir="/home/ise/Desktop/test/tiny-imagenet-200/train/",
                     val_dir="/home/ise/Desktop/test/tiny-imagenet-200/val/")