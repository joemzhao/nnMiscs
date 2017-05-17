from trim_generator import Generator as G
from discriminator import Discriminator as D
from dataloader import g_data_loader as G_ld
from dataloader import full_loader as F_ld
from rollout import ROLLOUT

import numpy as np
import tensorflow as tf
import random
import os

import helpers as hp
import fuse.trim_fuser as fuser


EMB_DIM = 80
HID_DIM = 64
START_TOKEN = 0
PRE_EPOCH_NUM = 5
SEED = 1234
BATCH_SIZE = 1
VOCAB_SIZE = 20526
LR = 0.01

dis_embedding_dim = 64
dis_filter_sizes = [1, 2]
dis_num_filters = [10, 20]
dis_dropout_keep_prob = 0.75
dis_l2_reg_lambda = 0.2
dis_batch_size = 64

data_path = "./datasets/bbt_concate_full.txt"
out_file = "./save/generated.txt"

pretrain_save = "/pretrained/"+str(PRE_EPOCH_NUM)+"model.ckpt"

pretrain_loss = []
pretrain_loss_save = open("./pretrained/pretrain_loss_save.txt", "w")
def main():
    random.seed(SEED)
    np.random.seed(SEED)

    full_loader = F_ld()
    Q, real_A, candidates, cand_max_len = full_loader.pad_candidates()

    generator = G(cand_max_len=cand_max_len, emb_dim=80)
    discriminator = D(sequence_length=len(real_A), filter_sizes=dis_filter_sizes, num_filters=dis_num_filters)

    pre_G_dataloader = G_ld(BATCH_SIZE, cand_max_len, data_path)
    pre_G_dataloader.create_batches()

    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    writer =  tf.summary.FileWriter('./graph_log/', sess.graph)

    print "Pretraining the generator ... "
    for epoch in xrange(PRE_EPOCH_NUM):
        loss = hp.pre_train_epoch(sess, generator, pre_G_dataloader, candidates)
        if epoch % 1 == 0:
            cwd = os.getcwd()
            print "This is generator pretrain epoch %d: " % epoch
            print loss
            pretrain_loss.append(loss)

    for item in pretrain_loss:
        pretrain_loss_save.write(str(item)+", ")
    pretrain_loss_save.close()

    print "====== Finish pretraining of generator ======"

    print "Pretraining the discriminator ... "
    nega_A = hp.generate_samples(sess, generator, candidates, out_file)[0]
    feed = hp.get_dict_D(discriminator, nega_A, real_A)
    for _ in xrange(10):
        _, pre_d_loss = sess.run([discriminator.train_op, discriminator.loss], feed_dict=feed)
    print "====== Finish pretraining of discriminator ======"

    print "///// begin of adversarial training /////"
    rollout = ROLLOUT(generator, 0.8)
    for _ in xrange(20):
        for g_it in xrange(5):
            samples = generator.generate(sess, candidates)
            rewards = rollout.get_reward(sess, samples, cand_max_len-1, discriminator, candidates)
            feed = { generator.x: samples,
                     generator.rewards: rewards,
                     generator.begin_ad: True,
                     rollout.lstm.fuser.input_ph: np.expand_dims(np.asarray(candidates), axis=0)}
            _ = sess.run(generator.g_updates, feed_dict=feed)

        rollout.update_params()

        for d_it in xrange(1):
            nega_A = hp.generate_samples(sess, generator, candidates, out_file)[0]
            feed = hp.get_dict_D(discriminator, nega_A, real_A)
            _, pre_d_loss = sess.run([discriminator.train_op, discriminator.loss], feed_dict=feed)

        print "------ round summary --------"
        g_gan_loss = hp.loss_checker(sess, generator, pre_G_dataloader, candidates)
        print "Results of GAN:"
        print g_gan_loss
        samples = generator.generate(sess, candidates)
        hp.translator(Q, real_A, samples[0])
        print "-----------------------------"

if __name__ == "__main__":
    main()
