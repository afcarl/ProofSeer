from sklearn import preprocessing
import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout
from keras.models import load_model
from keras.layers.recurrent import LSTM, GRU
import random
from random import randint
import matplotlib.pyplot as plt
from scipy import spatial
import linecache
import os
import time

from keras.wrappers.scikit_learn import KerasClassifier

from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline

from cStringIO import StringIO



def predictWordByContext(context):
    return 1


def clean_text(token):

    token = token.replace(",", "")
    token = token.replace(".", "")
    token = token.replace("?", "")
    token = token.replace(":", "")
    token = token.replace(";", "")
    token = token.replace("\"", "")
    token = token.replace(")", "")
    token = token.replace("(", "")
    token = token.replace("[", "")
    token = token.replace("]", "")
    token = token.replace("}", "")
    token = token.replace("{", "")
    return token


def my_strip(token):
    token = token.strip(",")
    token = token.strip(".")
    token = token.strip("?")
    token = token.strip(":")
    return token


def tokenize_file_to_vectors(common_words_file, file2tokenize, outputfile):
    with open(file2tokenize) as f:
        for line in f:
            line = line.lower()
            tokens = line.split()
            if (len(tokens) > 4):
                five_gramms = find_ngrams(line, 5)
                for gramm in five_gramms:
                    str_gramm = get_csv(gramm)
                    with open(outputfile, "a") as myfile:
                        myfile.write(str_gramm)


def get_tokenized_file_to_vectors2(vocab, file2tokenize):
    tokenized_file = ""
    with open(file2tokenize) as f:
        for line in f:
            line = line.lower()
            tokens = line.split()
            if len(tokens) > 10:
                n_grams = find_ngrams(line, 11)
                for gram in n_grams:
                    current_y = gram[5]
                   # current_y = clean_text(current_y)
                    if current_y in vocab:
                        str_gramm = get_csv(gram, vocab, 5, 11)
                        tokenized_file = tokenized_file + str_gramm
    return tokenized_file


def get_tokenized_file_to_vectors(vocab, file2tokenize):
    tokenized_file = ""
    with open(file2tokenize) as f:
        for line in f:
            line = line.lower()
            tokens = line.split()
            if len(tokens) > 4:
                five_gramms = find_ngrams(line, 5)
                for gramm in five_gramms:
                    current_y = gramm[2]
                    current_y = clean_text(current_y)
                    if current_y in vocab:
                        str_gramm = get_csv(gramm, vocab, 2, 5)
                        tokenized_file = tokenized_file + str_gramm
    return tokenized_file


def get_csv(gramm, vocab, target_index, n_gram_size): #target index is the middle word in window. context-leaf and context-right are same length.
    xs = get_xs(gramm, target_index, vocab, n_gram_size)
    ys = get_ys(gramm, target_index, vocab)
    result = xs + " , " + ys + "\n"
    return result


def get_xs(gramm, exclude_index, vocab, n_gram_size):

    xs = ["0"] * 10000
    for i in range(0, n_gram_size, 1):
        if i != exclude_index:
            index = find_word_index_in_list(gramm[i], vocab)
            if (index != -1):
                xs[index] = "1"
              # print(index)
    return ','.join(str(e) for e in xs)


def get_ys(gramm, label_index, vocab):
    ys = ["0"] * 10000
    index = find_word_index_in_list(gramm[label_index], vocab)
    if (index != -1):
        ys[index] = "1"
    return ','.join(str(e) for e in ys)


def find_word_index(word, common_words_filename):

    count = 0
    if len(word) > 0:
        with open(common_words_filename) as f:
            for line in f:
                tokens = line.split()
                # print(str(len(tokens)))
                if tokens[0] == word:
                    return count
                count = count +1
    else:
        print("Empty token")
    #return -1 if the word was not found in the list of most common words
    return -1

def read_vocab_to_list(filename):
    return [word for line in open(filename, 'r') for word in line.split()]


def find_word_index_in_list(word, word_list):
    if word in word_list:
        return word_list.index(word)
    return -1


def write_common_files():
    with open("/Users/macbook/Desktop/corpora/magic.txt", "a") as myfile:
         with open("/Users/macbook/Desktop/corpora/common_words_coca.txt") as f:
            for line in f:
                tokens = line.split()
                for i in range(0, 4999, 1):
                    print("writing: " + tokens[i][3:])
                    myfile.write(tokens[i][3:] + "\n")





def find_ngrams(s, n):
    input_list = s.split(" ")
    for i in range(0, len(input_list), 1):
        input_list[i] = clean_text(input_list[i])
    return zip(*[input_list[i:] for i in range(n)])


def create_online_dataset(filename):

    np.genfromtxt(StringIO(filename), delimiter=",")





def train_model_from_dir(root, vocabulary_filename):

    start_time = time.time()
    print("Creating the model object")
    model = Sequential()
    model.add(Dense(10, input_dim=10000, init='uniform', activation='relu'))
    model.add(Dense(10000, init='normal', activation='softmax'))  # can be also sigmoid (for a multiclass)
    print("compiling...")
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    print("compiled!")
    count = 0
    for path, subdirs, files in os.walk(root):
        for name in files:
            current_filename = os.path.join(path, name)
            if current_filename.endswith("txt"):
                count = count + 1
                print("file number", count)
                file_start = time.time()
                data = get_tokenized_file_to_vectors2(vocabulary_filename, current_filename)
             #   print("read file:", count)
                dataset = np.genfromtxt(StringIO(data), delimiter=",")
             #   print("shape", dataset.shape)
                if (len(dataset.shape) == 2 and dataset.shape[1] == 20000):
                    X = dataset[:, 0:10000]
                    Y = dataset[:, 10000:]
                    arrX = np.array(X)
                    arrY = np.array(Y)
                    model.fit(arrX, arrY, nb_epoch=50, batch_size=dataset.shape[0]) #check the batch size
                    log_train_file(current_filename, dataset.shape[0])
                else:
                    log_fail_file(current_filename)
                file_end = time.time()
                print("file time:", file_end - file_start)
                if count % 10 == 0:
                    print("Saving model...", count)
                    model.save("C:\corpora\\model.h5")
    end_time = time.time()
    print("elapsed time", end_time - start_time)
    model.save("C:\corpora\\model.h5")


def continue_train_model_from_dir(root, vocabulary_filename, model_filename):

    start_time = time.time()
    model = load_model(model_filename)
    count = 0
    for path, subdirs, files in os.walk(root):
        for name in files:
            current_filename = os.path.join(path, name)
            if current_filename.endswith("txt"):
                count = count + 1
                if find_word_index(current_filename, "C:\corpora\\log.txt") == -1:
                    print("file number", count)
                    print("filename", current_filename)
                    file_start = time.time()
                    data = get_tokenized_file_to_vectors2(vocabulary_filename, current_filename)
                    dataset = np.genfromtxt(StringIO(data), delimiter=",")
                    print("shape dim:", len(dataset.shape))
                    if (len(dataset.shape) ==2 and dataset.shape[1]==20000):
                        X = dataset[:, 0:10000]
                        Y = dataset[:, 10000:]
                        arrX = np.array(X)
                        arrY = np.array(Y)
                        model.fit(arrX, arrY, nb_epoch=50, batch_size=dataset.shape[0]) #check the batch size
                        log_train_file(current_filename, dataset.shape[0])
                    else:
                        log_fail_file(current_filename)
                    file_end = time.time()
                    print("file time:", file_end - file_start)
                    if count % 10 == 0:
                        print("Saving model...", count)
                        model.save("C:\corpora\\model.h5")
                else:
                    print("file already trained:", count, current_filename)
    end_time = time.time()
    print("elapsed time", end_time - start_time)
    model.save("C:\corpora\\model.h5")


def log_train_file(filename, tokens_num):
     log_file = "C:\corpora\\log.txt"
     logline = filename + " " + str(tokens_num) + "\n"
     with open(log_file, "a") as myfile:
         myfile.write(logline)


def log_fail_file(filename):
    log_file = "C:\corpora\\log_fail.txt"
    logline = filename  + "\n"
    with open(log_file, "a") as myfile:
        myfile.write(logline)

def test_model_on_dir(model_filename, root, vocab):
    model = load_model(model_filename)
    average = 0
    files_num = 0
    for path, subdirs, files in os.walk(root):
        for name in files:
          #  print("file name", os.path.join(path, name))
            if (name.endswith("txt")):
                data = get_tokenized_file_to_vectors2(vocab, os.path.join(path, name))
                dataset = np.genfromtxt(StringIO(data), delimiter=",")
                X = dataset[:, 0:10000]
                Y = dataset[:, 10000:]
                arrX = np.array(X)
                arrY = np.array(Y)
                predictions = model.predict(arrX)
              #  mrr = getMRR_after_sort(predictions, arrY, arrX, vocab)
                mrr = getMRR(predictions, arrY)
                average = average + mrr
                files_num = files_num + 1
                print(name, "MRR:", mrr)
    print ("Average MRR:", average/files_num)



def getMRR(predictions, labels):
    sum = 0
    for i in range(0, len(predictions), 1):
        correct_index = np.argmax(labels[i])
        predicted_index = np.argmax(predictions[i])
        rank = 1
        while predicted_index != correct_index and rank < len(predictions):
            predictions[i][predicted_index] = -1
            predicted_index = np.argmax(predictions[i])
            rank = rank + 1
        if rank < len(predictions)-1:
            sum = sum + 1/float(rank)
    return sum/float(len(predictions))


def getMRR_after_sort(predictions, labels, contexts, vocab):
    sum = 0
    for i in range(0, len(predictions), 1):
        correct_index = np.argmax(labels[i])
        sorted_predictions = get_top_sorted_predictions_indexes(predictions[i], contexts[i], vocab, correct_index) #sorted 1-dimensional array of suggestions
        rank = 1
        predicted_index = sorted_predictions[0]
        while predicted_index != correct_index and rank < len(sorted_predictions):
            predicted_index = sorted_predictions[rank]
            rank = rank + 1
        if rank < len(sorted_predictions):
            sum = sum + 1/float(rank)
    return sum/float(len(predictions))


def get_top_sorted_predictions_indexes(prediction, context, vocab, correct_index):
    sorted_predictions = [0] * 5
    top_ten_indices = [0] * 5
    for i in range(0, 5, 1):
        max_probability_index = np.argmax(prediction)
        top_ten_indices[i] = max_probability_index
        prediction[max_probability_index] = -1

    top_ten_words = []
    for index in top_ten_indices:
        top_ten_words.append(vocab[index])

  #  print("top ten words", top_ten_words)
    top_ten_vectors = []
    for word in top_ten_words:
        vector = get_vector(word)
        top_ten_vectors.append(vector)
   # print("top ten vec length", len(top_ten_vectors))

    context_indexes = np.where(context == 1)
 #   print ("context indexes", context_indexes)
    context_words = []
    for index in context_indexes[0]:
        context_words.append(vocab[index])
 #   print ("Context words", context_words)

    context_vectors = []
    for word in context_words:
        vector = get_vector(word)
        context_vectors.append(vector)
 #   print("length context vectors", len(context_vectors))

    correct_vector = get_vector(vocab[correct_index])
    context_similarities = []
    for vector in top_ten_vectors:
        vector_sim = 0
        vector_sim = vector_sim + 1 - spatial.distance.cosine([float(i) for i in vector], [float(i) for i in correct_vector])
        context_words_num = 0
        for context_vec in context_vectors:
            vector_sim = vector_sim + 1 - spatial.distance.cosine([float(i) for i in vector], [float(i) for i in context_vec])
            context_words_num = context_words_num + 1
        grade = 0
        grade = vector_sim / float(float(context_words_num)+1)
        context_similarities.append(grade)
    decorated = zip(top_ten_indices, context_similarities)
    list_of_lists = [list(elem) for elem in decorated]
    sorted_predictions = sorted(list_of_lists, key=lambda pair: pair[1], reverse=True)
    list1, list2 = zip(*sorted_predictions)
    return list1


def get_vector(token, extra_vectors_file="/Users/macbook/Desktop/corpora/aux_files/extra_vocab.txt"):
    config = RNNGloveConfig()
    with open(extra_vectors_file) as f:
        for line in f:
            tokens = line.split()
            if tokens[0] == token.lower():
                vec = tokens[1:config.vector_dimension+1]
    #            print ("returning from extra: ", token)
                return vec
    with open(config.glove_vectors) as f:
        for line in f:
            tokens = line.split()
            if tokens[0] == token.lower():
                vec = tokens[1:config.vector_dimension+1]
                return vec
    vec = add_unseen_token_2_extra_vocabulary(token, extra_vectors_file)
    return vec


def add_unseen_token_2_extra_vocabulary(token, extra_vocab_filename):
    config = RNNGloveConfig()
 #   print("Adding unseen token: ", token)
    random_vector = [random.random() for _ in range(0, config.vector_dimension)]
    string_vector = [str(i) for i in random_vector]
    vector = [token.lower()] + [" "] + string_vector
    with open(extra_vocab_filename, "a") as myfile:
        str_vector = ' '.join(str(e) for e in vector) #covert list to string
        str_vector = str_vector + "\n"
        myfile.write(str_vector)
    return random_vector


def get_context_words(context):
    words = [""] * 5
    return words

class RNNGloveConfig(object):
    vector_dimension = 50
    epochs_number = 50
    glove_vectors = "/Users/macbook/Desktop/corpora/aux_files/glove.6B.50d.txt"

def main():

    print("haha")

    common_words_filename = "C:\corpora\\clean_vocab10000.txt"
    vocab = read_vocab_to_list(common_words_filename)
    corpus_path = "C:\corpora\\clean_corpus"
 #   train_model_from_dir(corpus_path, vocab)
 #   dense_vectors_glove = "/Users/macbook/Desktop/corpora/aux_files/glove.6B.50d.txt"
 #   one_hot_train_data = "/Users/macbook/Desktop/corpora/aux_files/one_hot_csv.txt"
  #  continue_train_model_from_dir(corpus_path, vocab, "C:\corpora\\model.h5")
#    test_model_on_dir("C:\\corpora\\model.h5", "C:\\corpora\\alt_test", vocab)
 #   test_model_on_dir("C:\\corpora\\model.h5", "C:\\corpora\\alt_test2", vocab)
    test_model_on_dir("C:\\corpora\\model.h5", "C:\\corpora\\triple_test_clean", vocab)


  #  print(data)
   # print (x)


if __name__ == "__main__":
    main()
