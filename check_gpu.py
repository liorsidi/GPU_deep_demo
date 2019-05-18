#this code checks if the GPU is configured on the machine
import tensorflow as tf
print(tf.test.is_gpu_available(cuda_only=False,min_cuda_compute_capability=None))

from tensorflow.python.client import device_lib
local_device_protos = device_lib.list_local_devices()
print local_device_protos

