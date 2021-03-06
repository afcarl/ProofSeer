from _gdynet import *
import _gdynet as dy
#from dynet import *
#import dynet as dy
import time
import random
import numpy as np
from sklearn import model_selection
from sklearn.metrics import roc_auc_score

LAYERS = 2
INPUT_DIM = 50 #50  #256
HIDDEN_DIM = 50 # 50  #1024
VOCAB_SIZE = 0

from collections import defaultdict
from itertools import count
import sys
import util


class RNNLanguageModel:
    def __init__(self, model, LAYERS, INPUT_DIM, HIDDEN_DIM, VOCAB_SIZE, builder=SimpleRNNBuilder):

        self.builder = builder(LAYERS, INPUT_DIM, HIDDEN_DIM, model)
        self.lookup = model.add_lookup_parameters((VOCAB_SIZE, INPUT_DIM))
        self.R = model.add_parameters((2, HIDDEN_DIM))
        self.bias = model.add_parameters((2))

    def save2disk(self, filename):
        model.save(filename, [self.builder, self.lookup, self.R, self.bias])

    def load_from_disk(self, filename):
        (self.builder, self.lookup, self.R, self.bias) = model.load(filename)

    def build_sentence_graph(self, sent, label):
        renew_cg()
        init_state = self.builder.initial_state()

        R = parameter(self.R)
        bias = parameter(self.bias)
        errs = [] # will hold expressions
        state = init_state
        for i in range(0, len(sent)-1):
            # assume word is already a word-id
            x_t = lookup(self.lookup, int(sent[i]))
            state = state.add_input(x_t)

        y_t = state.output()
        r_t = bias + (R * y_t)
        err = pickneglogsoftmax(r_t, label)
        errs.append(err)
        nerr = esum(errs)
        return nerr


    def predict_class(self, sentence):
        renew_cg()
        init_state = self.builder.initial_state()
        R = parameter(self.R)
        bias = parameter(self.bias)
        state = init_state
        for cw in sentence:
            # assume word is already a word-id
            x_t = lookup(self.lookup, int(cw))
            state = state.add_input(x_t)
        y_t = state.output()
        r_t = bias + (R * y_t)
        prob = softmax(r_t)
        return prob


    def sample(self, first=1, nchars=0, stop=-1):
        res = [first]
        renew_cg()
        state = self.builder.initial_state()

        R = parameter(self.R)
        bias = parameter(self.bias)
        cw = first
        while True:
            x_t = lookup(self.lookup, cw)
            state = state.add_input(x_t)
            y_t = state.output()
            r_t = bias + (R * y_t)
            ydist = softmax(r_t)
            dist = ydist.vec_value()
            rnd = random.random()
            for i,p in enumerate(dist):
                rnd -= p
                if rnd <= 0: break
            res.append(i)
            cw = i
            if cw == stop: break
            if nchars and len(res) > nchars: break
        return res


def log_train_file(message, error):
    log_file = "C:\\corpora\\log.txt"
    logline = message + " " + str(error) + "\n"
    with open(log_file, "a") as myfile:
        myfile.write(logline)


def readY(fname):
    train = []
    with file(fname) as fh:
        for line in fh:
            line = line.lower()
            train.append(int(line.strip()[-1]))
    return train

if __name__ == '__main__':

    filename = "C:\\corpora\\yahoo\\Title_3.csv"
    train = util.FastCorpusReaderYahoo(filename)
    vocab = util.Vocab.from_corpus(train)

    Ys = readY(filename)
    train = list(train)
    for i in range(0, len(train)):
        print train[i], Ys[i]


    VOCAB_SIZE = vocab.size()
    print ("vocab_size", VOCAB_SIZE)

    dy.init()
    print "DyNet was initialized, starting train"


    recall_1_list = []
    recall_0_list = []
    loss = 0
    n = len(train)
    auc = []

    kf = model_selection.KFold(n_splits=5)
    for train_idx, test_idx in kf.split(train):

        model = Model()
        sgd = AdamTrainer(model)
        lm = RNNLanguageModel(model, LAYERS, INPUT_DIM, HIDDEN_DIM, VOCAB_SIZE, builder=LSTMBuilder)


        X_train =  [train[i] for i in train_idx]
        Y_train = [Ys[i] for i in train_idx]

        X_test = [train[i] for i in test_idx]
        Y_test = [Ys[i] for i in test_idx]
        #TRAIN
        for ITER in xrange(3):  # number of epochs
            for i, sentence in enumerate(X_train):
                print sentence
                isent = [vocab.w2i[w] for w in sentence]
                errs = lm.build_sentence_graph(isent, Y_train[i])
                loss += errs.scalar_value()
                errs.backward()
                sgd.update()
                sgd.status()
                sgd.update_epoch()
        #TEST
        correct_0 = 0
        count_0 = 0
        correct_1 = 0
        count_1 = 0
        all_0 = 0
        all_1 = 0
        classified_as_1 = 0
        classified_as_0 = 0

        res = []
        for i, sentence in enumerate(X_test):
            isent = [vocab.w2i[w] for w in sentence]
            sent = isent[0:len(isent) - 1]
            label = Y_test[i]
            probs = lm.predict_class(isent)
            distribution = probs.npvalue()
            answer = np.argmax(distribution)
            res.append(answer)
            if answer == 0 and label == 0:
                correct_0 += 1

            if answer == 1 and label == 1:
                correct_1 += 1

            if answer == 0:
                all_0 += 1
            else:
                all_1 += 1

            if label == 1:
                count_1 += 1
            else:
                count_0 += 1
            print sent, label, answer

        auc.append(roc_auc_score(Y_test, res))
        recall_1_list.append(correct_1 / float(count_1))
        recall_0_list.append(correct_1 / float(count_0))

    print "RECALL 1 list:", recall_1_list
    print "RECALL 0 list:", recall_0_list

    print "RECALL 1:", sum(recall_1_list) / float(len(recall_1_list))
    print "RECALL 0:", sum(recall_0_list) / float(len(recall_0_list))
    print "AUC :", sum(auc)/float(len(auc))
    