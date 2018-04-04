# import keras
#import sys
#import h5py
import os
from collections import defaultdict

from keras import models, layers, optimizers
from keras.layers import Embedding, LSTM, Dense, Dropout, Merge, Flatten
from keras.models import Sequential
import numpy as np
import logging

from keras.applications.vgg19 import VGG19
from keras.preprocessing import image
from keras.applications.vgg19 import preprocess_input
from keras.models import Model
import pandas as pd




LOGNAME = "vqa"
logger = logging.getLogger(LOGNAME)
logger.level = logging.DEBUG


fileHandler = logging.FileHandler("{0}.log".format(LOGNAME))
consoleHandler = logging.StreamHandler()
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

def Image2Features(image_path, base_model=None):
    base_model = base_model or VGG19(weights='imagenet')
    model = Model(inputs=base_model.input, outputs=base_model.get_layer('block4_pool').output)
    img = image.load_img(image_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    block4_pool_features = model.predict(x)
    return block4_pool_features


def Word2VecModel(embedding_matrix, num_words, embedding_dim, seq_length, dropout_rate):
    # notes:
    # num works: scalar represents size of original corpus
    # embedding_dim : dim reduction. every input string will be encoded in a binary fashion using a vector of this length
    # embedding_matrix (AKA embedding_initializers): represents a pre trained network

    LSTM_UNITS = 512
    DENSE_UNITS = 1024
    DENSE_ACTIVATION = 'tanh'

    logger.debug("Creating Text model")
    model = Sequential()

    layer = Embedding(num_words,embedding_dim,weights=[embedding_matrix],input_length=seq_length,trainable=False)
    model.add(layer)

    lstm1 = LSTM(units=LSTM_UNITS,return_sequences=True,input_shape=(seq_length,embedding_dim))
    model.add(lstm1)

    dropout1 = Dropout(rate=dropout_rate)
    model.add(dropout1)

    lstm2 = LSTM(units=LSTM_UNITS, return_sequences=False)
    model.add(lstm2)

    dropout2 = Dropout(rate=dropout_rate)
    model.add(dropout2)

    dense = Dense(units=DENSE_UNITS, activation=DENSE_ACTIVATION)
    model.add(dense)
    return model

def img_model(dropout_rate):
    DENSE_UNITS = 1024
    INPUT_DIM = 4096
    DENSE_ACTIVATION = 'tanh'
    logger.debug("Creating image model")
    model = Sequential()
    dense = Dense(units=DENSE_UNITS, input_dim=INPUT_DIM, activation=DENSE_ACTIVATION)
    model.add(dense)
    return model


def vqa_model(embedding_matrix, num_words, embedding_dim, seq_length, dropout_rate, num_classes):
    MERGE_MODE = 'mul'
    DENSE_UNITS = 1000
    DENSE_ACTIVATION = 'tanh'

    OPTIMIZER = 'rmsprop'
    LOSS = 'categorical_crossentropy'
    METRICS = 'accuracy'
    vgg_model = img_model(dropout_rate=dropout_rate)
    lstm_model = Word2VecModel(embedding_matrix=embedding_matrix, num_words=num_words, embedding_dim=embedding_dim,
                               seq_length=seq_length, dropout_rate=dropout_rate)
    logger.debug("merging final model")
    fc_model = Sequential()

    merge = Merge([vgg_model,lstm_model], mode=MERGE_MODE)
    fc_model.add(merge)

    dropout1 = Dropout(dropout_rate)
    fc_model.add(dropout1)

    dense1 = Dense(units=DENSE_UNITS, activation=DENSE_ACTIVATION)
    fc_model.add(dense1)

    dropout2 = Dropout(dropout_rate)
    fc_model.add(dropout2)

    dense2 = Dense(units=num_classes, activation='softmax')
    fc_model.add(dense2)

    fc_model.compile(optimizer=OPTIMIZER,loss=LOSS, metrics=METRICS)
    return fc_model

# segmentation: {'counts': 'j19[6h1ZNXNf1h1ZNYNe1g1[NYNf1f1YNZNh1e1YN^Nd1b1ZNbNd1^1ZNdNf1\\1ZNdNf1\\1ZNdNlKLo4_1UOBj0>kNNRLUNi4l1UO0RLUNh4k1UO;l0DTO<R1^OnNb0R1^OnNc0T1ZOlNg0X1TOhNm0V1SOkNm0T1TOlNl0T1TOjNbNmKZ2X5UOkNm0V1ROkNm0T1TOlNk0U1UOlNj0T1UOmNk0S1UOmNk0S1UOmNk0S1UOmNl0R1TOoNk0l0gMmJ01^1W4j0j0kMoJ[1W4j0j0kMoJ[1X4i0a0UNVKQ1Z4j0`0D@<`0D@<`0D@<`0D@<`0D@<`0D@=?CA=?BB>=CC==CB>:FF:?A@`0a0_O_Oa0b0^O_Ob0`0^O_Oc0a0]O@b0`0]OCa0<@D`0;AE?:BG=8DI;7EI<6DK;1I06OJ35MK35MK35MK35MK35MK45KK55KK55KK55KK64JK75IK75IK75IK75IK75IK84HL85GJ:6FJ:6FJ;5EK;5EK;5EK;5EK;5EK:7EI;7EH;9EG::FF9;GE9;GE9;GE9<EE:<FD:<FC;=EC=;CE=;CE<<DD<<DD=;CE=<BD?WNWKM5k1U41P1JPO6P1JoN7Q1IoN7Q1IoN7R1HnN8Q1JnN5S1KmN5S1KmN5S1KmN5T1JlN6T1JlN6T1JlN6S1KlN6P1SNkJg1U45n0WNmJe1T44o0XNlJd1U44o0XNkJe1V43o03QOMm0TNmJo1V4Mj08VOHi0:VOFk09UOGk09UOGk09UOFl0:SOGn08ROHn08ROHn08ROHn08UOEk0;WOCk0;VODk0<TOWNgKR1Y5c0ROYNeKT1Y5c0oNZNjKS1W5c0nNZNUMJn3k1nNZNb2f1aMWN_2j1aMSNeKOk6m1`40000002N1O2N01N10000O010O10002N001O000010O0000O10001M2L`D\\Nb;c1301VOZDMh;L_DEP<J`me33\\SZL5L4K5L4L5G8J8I4fNaNcF_1[9cNeF]1[9cNbF`1]9cNaELl0f1^9_NfELk0e1_9cNbF\\1^9dNaF]1_9dN`F\\1`9dN`F\\1`9dN`F\\1`9eN_F[1U8UORGTO<<=Z1Q8ZNVGQ1:]O?X1o7BaGTO`0Z1j7`0TH@i7R3000000000O100000001O0O2I7eNZ1ZNf10001O000001O01O00O11O3N0O000MRDkNm;U1TDjNm;U14O101M_Eb0Z7]OgHb0[7]OeHc0[7]OeHc0[7^OdHb0\\7^OdHb0]7]OcHc0]7]OcHc0]7]OcHb0b7YO_Hg0c7UO_Hl0a7UO]Hj0k7oNUHQ1l7nNTHQ1m7kNWHU1o900000O1O01000O10_NZD^10aNg;a10000O10000000001O000`dU1', 'size': [426, 640]}
# area: 25483.0
# iscrowd: 0
# image_id: 139
# bbox: [0.0, 38.0, 549.0, 297.0]
# category_id: 98
# id: 20000000


def try_run_lstm_model(lstm_model,seq_length):
    set_1 = np.array(["Hello World!", "To infinite and beyond!", "so, we meet again mister Bond",
                                    "To boldly go where no one has gone before",
                                    "This list length has {seq_length} items"])

    set_2= np.array(["Each", "word", "is", "an", "item"])

    set_3 = np.array([1, 2, 3, 4, 5])

    res = defaultdict(lambda :[])
    template = "{0}:\n\t\t{1}"
    for s in [set_1, set_2, set_3]:
        try:
            assert len(s) == seq_length, "got an unexpected set length {0}".format(len(s))
            p = lstm_model.predict(s)
            res["SUCCESS"].append(template.format(s,p))
        except Exception as ex:
            res["Failed"].append(template.format(s,ex))

    return res

def images_to_embedded(images_path):
    COL_IMAGE = 'image'
    COL_PATH = 'full_path'
    COL_EMBEDDED = 'embedded'
    images_files = [os.path.join(images_path, fn) for fn in os.listdir(images_path) if fn.lower().endswith('jpg')]
    df = pd.DataFrame(columns=[COL_IMAGE, COL_PATH, COL_EMBEDDED])
    df.set_index(COL_IMAGE)
    df[COL_PATH] = images_files
    image_from_path = lambda path: os.path.split(path)[1]
    df[COL_IMAGE] = df[COL_PATH].apply(image_from_path)
    # # This causes out of memory
    base_model = VGG19(weights='imagenet')
    length_df = len(df)

    global embeded_idx
    embeded_idx = 0
    def get_embedded(fn):
        global embeded_idx
        logger.debug("embedded {0}/{1}".format(embeded_idx + 1, length_df))
        embeded_idx += 1
        try:
            embedded  = Image2Features(fn,base_model=base_model )
        except Exception as ex:
            embedded = None
            logger.warning("Failed on embedded {0}:\n{1}".format(embeded_idx + 1, ex))
        return embedded

    df['embedded'] = df['full_path'].apply(get_embedded)
    # length_df = len(df)
    # logger.debug("getting embedded for {0} images".format(length_df))
    # base_model = VGG19(weights='imagenet')
    # for i, row in df.iterrows():
    #     try:
    #         logger.debug("embedded {0}/{1}".format(i + 1, length_df))
    #         image_full_path = df.get_value(i, COL_PATH)
    #         embedded = Image2Features(image_full_path, base_model=base_model )
    #     except Exception as ex:
    #         embedded = None
    #         logger.warning("Failed on embedded {0}:\n{1}".format(i + 1, ex))
    #     df.set_value(i, COL_EMBEDDED, embedded)
    dump_path = os.path.join(images_path, 'embbeded_images.hdf')
    df.to_hdf(dump_path, key='image')
    return dump_path

def train_nn(train_features, train_labels,validation_features, validation_labels, batch_size=20,epochs=20):

    input_shape = train_features[0].shape#train_features.shape + train_features[0].shape #(train_features.shape[0],train_features[0].shape)
    #-------------------------------------------------------------------------------------
    model = models.Sequential()
    # model.add(layers.Dense(512, activation='relu', input_dim=7 * 7 * 512))
    model.add(layers.Dense(512, activation='relu', input_shape=input_shape))
    model.add(layers.Dropout(0.5))
    model.add(layers.Dense(3, activation='softmax'))



    #-------------------------------------------------------------------------------------------
    # define the architecture of the network
    model = Sequential()
    model.add(Flatten(input_shape=input_shape ,name='flatten'))
    model.add(Dense(768, activation="relu",name='dense_1'))#init="uniform",input_dim=3072
    # model.add(Dense(384, activation="relu",name='dense_2'))#init="uniform",
    # model.add(Dense(1,name='dense_3'))
    model.add(layers.Activation("relu",name='activation_out_layer'))# model.add(layers.Activation("softmax"))


    # -------------------------------------------------------------------------------------------
    model.compile(optimizer=optimizers.RMSprop(lr=2e-4),loss='sparse_categorical_crossentropy',metrics=['acc'])#,loss='categorical_crossentropy'


    # import itertools
    # a = list(itertools.chain.from_iterable(train_features))
    history = model.fit(train_features,
                        train_labels,
                        epochs=epochs,
                        batch_size=batch_size,
                        validation_data=(validation_features, validation_labels))

    # print(history)
    # raise Exception("success!:\n\n{0}".format(str(history))
    # )
    return model, history

def train_tag(tag):
    from pre_processing.known_find_and_replace_items import all_tags
    assert tag in all_tags, "{0} is not a valid tag\n(Valid Tags:\t{1})".format(tag, all_tags)

    from parsers.VQA18 import Vqa18Base
    from pre_processing.known_find_and_replace_items import train_data, validation_data, test_data

    data_locations = [train_data, validation_data, test_data][:2]

    nn_train_data = []
    for dl in data_locations:
        logger.debug("Getting data for: {0}".format(dl.data_tag))
        test_inst = Vqa18Base.get_instance(dl.processed_xls)
        data = test_inst.data
        embedding = pd.read_hdf(dl.embedding)
        embedding[Vqa18Base.COL_IMAGE_NAME] = embedding['image'].apply(lambda s: s.rstrip('.jpg'))

        # data.set_index(Vqa18Base.COL_IMAGE_NAME)
        # embedding.set_index(Vqa18Base.COL_IMAGE_NAME)

        data.reset_index(inplace=True)
        embedding.reset_index(inplace=True)
        dfMerged = pd.merge(data, embedding,
                            left_on=[Vqa18Base.COL_IMAGE_NAME],
                            right_on=[Vqa18Base.COL_IMAGE_NAME],
                            how='inner')

        # logger.debug("data colums:\n{0}".format(data.columns))
        # logger.debug("merged colums:\n{0}".format(dfMerged.columns))
        features = dfMerged['embedded']
        labels = dfMerged[tag]

        features = np.concatenate(np.asanyarray(features),axis=0)
        labels = np.asanyarray(labels)

        nn_train_data.append((features,labels))

    logger.debug("Got data for training NN")

    train_features , train_labels = nn_train_data[0]
    validation_features, validation_labels = nn_train_data[1]




    model, history = train_nn(train_features=train_features
                              ,train_labels=train_labels
                              ,validation_features=validation_features
                              ,validation_labels=validation_labels)#.tolist()

    model_fn = '{0}_model.h5'.format(tag)
    logger.debug("saving model for: {0}".format(tag))
    model.save(model_fn)  # creates a HDF5 file 'my_model.h5'
    logger.debug("model saved")
    # # returns a compiled model
    # # identical to the previous one
    # model = load_model('my_model.h5')
    str()






def main():
    train_tags, do_images_to_embedded, words_2_embedded = [True, False, False]
    #### Train tags ----------------------------------------------------------------------------------------------------
    if train_tags:
        from pre_processing.known_find_and_replace_items import all_tags
        for t in all_tags:
            try:
                logger.warning("Train tag {0}.".format(t))
                train_tag(t)
                logger.warning("Done train tag {0}.".format(t))
            except Exception as ex:
                logger.warning("Failed to train tag {0}:\n{1}".format(t,ex))
    #### END OF Train tags ----------------------------------------------------------------------------------------------------

    #### Images to embedded --------------------------------------------------------------------------------------------
    if do_images_to_embedded:
        images_path_train = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Train\\VQAMed2018Train-images'
        images_path_validation ='C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Valid\\VQAMed2018Valid-images'
        images_path_test = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Test\\VQAMed2018Test-images'
        dump_path = images_to_embedded(images_path_test)
    #### END OF Images to embedded--------------------------------------------------------------------------------------

    #### words to embedded ---------------------------------------------------------------------------------------------
    if words_2_embedded:
        pass
        # path_to_weights = "C:\\Users\\Public\\Documents\\Data\\2017\\model_weights.h5"
        # with h5py.File(path_to_weights, "r") as f:
        #     embedding_matrix = f['/embedding_1/embedding_1_W']
        # #     for item in f.attrs.keys():
        # #         print("{0}: {1}\n".format(item ,f.attrs[item]))
        #     # str()
        #
        #     num_words = 12602#45185 #arbitraraly chose number of words in clef captions 2014 competition
        #     embedding_dim = 300#1000 # preaty much arbitrary
        #     seq_length = 5 # !!!!!! Not sure what is that...
        #     dropout_rate = 0.5 #picked up as naive default from an SO answer...
        #
        #     logger.debug("embedding_matrix shape: {0}".format(embedding_matrix.shape))
        #
        #     lstm_model = Word2VecModel(embedding_matrix=embedding_matrix, num_words=num_words, embedding_dim=embedding_dim,
        #                            seq_length=seq_length, dropout_rate=dropout_rate)
        #
        #
        #     results = try_run_lstm_model(lstm_model, seq_length)
        #     for k,v in results.items():
        #         print("{0}:\n\t{1}\n\n".format(k,"\n".join([s for s in v])))
    #### END OF words to embedded---------------------------------------------------------------------------------------





    # fileName = "prj_test.nexus.hdf5"
    # f = h5py.File(fileName,  "r")
    # for item in f.attrs.keys():
    #     print(item + ":", f.attrs[item])
    # mr = f['/entry/mr_scan/mr']
    # i00 = f['/entry/mr_scan/I00']
    # print("%s\t%s\t%s" % ("#", "mr", "I00"))
    # for i in range(len(mr)):
    #     print("%d\t%g\t%d" % (i, mr[i], i00[i]))
    # f.close()





if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Got an error:\n{0}".format(e))
        raise
        # sys.exit(1)