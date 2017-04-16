import numpy as np
import os

class config_D(object):
    def __init__(self):
        self.num_epoch = 15
        self.batch_size = 128
        self.lr = 0.01
        self.vocab_size = 20000
        self.embd_dim = 64
        self.hidden_dim = 64
        self.hidden_layer_num = 1
        self.max_len = 20
        self.class_number = 2
        self.keep_prob = 0.9
        self.max_grad_norm = 5.
        self.init_scale = 0.1
