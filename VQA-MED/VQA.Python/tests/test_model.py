import os
import tempfile
from keras import Model
from io import StringIO
import pandas as pd


from classes.vqa_model_builder import VqaModelBuilder
from classes.vqa_model_predictor import  VqaModelPredictor
from classes.vqa_model_trainer import VqaModelTrainer
from common.utils import VerboseTimer


loss, activation = 'categorical_crossentropy', 'sigmoid'

def test_model_creation():
    # loss, activation = 'categorical_crossentropy', 'softmax' # good for a model to predict multiple mutually-exclusive classes:
    # loss, activation = 'binary_crossentropy', 'sigmoid'


    with VerboseTimer("Instantiating VqaModelBuilder"):
        mb = VqaModelBuilder(loss, activation)

    with VerboseTimer("Instantiating VqaModelBuilder"):
        model = mb.get_vqa_model()


    model.summary()
    expected_fields = ['predict','fit']
    for field in expected_fields:
        assert hasattr(model, field), f'A model is expected to have a "{field}" attribute'


def test_model_training():
    epochs = 1
    batch_size = 75
    mb = VqaModelBuilder(loss, activation)
    model = mb.get_vqa_model()

    data_path = os.path.abspath(os.path.join('./data_for_test/train_data.hdf'))
    with pd.HDFStore('D:\\Users\\avitu\\Downloads\\train_data.hdf') as store:
        train_data = store['data']

    mt = VqaModelTrainer(model, use_augmentation=False, batch_size=batch_size, data_location=train_data)
    mt.train()

    mp = VqaModelPredictor(model)
    test_data = train_data
    predictions = mp.predict(train_data)
    preds = predictions.prediction
    ground_true = predictions.answer

    assert len(preds) == len(test_data), 'Got a different number for predictions input and output'




if __name__ == '__main__':
  # test_model_creation()
  test_model_training()
