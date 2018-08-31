import inspect
import os
import re
import textwrap
from collections import defaultdict

import pandas as pd
import cv2
import numpy as np

from common.settings import input_length, image_size, get_nlp
from common.settings import embedding_dim
from vqa_logger import logger

def get_size(file_name):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    nbytes = os.path.getsize(file_name)
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def get_highlited_function_code(foo, remove_comments=False):
    """
    Prints code of a given function with highlighted syntax in a jupyter notebook
    :rtype: IPython.core.display.HTML
    :param foo: the function to print its code
    :param remove_comments: should comments be remove
    """
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import HtmlFormatter
    import IPython

    txt = inspect.getsource(foo)
    if remove_comments:
        lines = txt.split('\n')
        lines = [l for l in lines if not l.lstrip().startswith('#')]
        txt = '\n'.join(lines)

    textwrap.dedent(txt)

    formatter = HtmlFormatter()
    ipython_display_object = \
        IPython.display.HTML('<style type="text/css">{}</style>{}'.format(
            formatter.get_style_defs('.highlight'),
            highlight(txt, PythonLexer(), formatter)))




    return ipython_display_object
    # print(txt)


def get_image(image_file_name):
    ''' Runs the given image_file to VGG 16 model and returns the
    weights (filters) as a 1, 4096 dimension vector '''
    im = cv2.resize(cv2.imread(image_file_name), image_size)

    # convert the image to RGBA
    #     im = im.transpose((2, 0, 1))
    return im


def get_text_features(txt):
    ''' For a given txt, a unicode string, returns the time series vector
    with each word (token) transformed into a 300 dimension representation
    calculated using Glove Vector '''
    # print(txt)
    try:

        nlp = get_nlp()
        tokens = nlp(txt)
        text_features = np.zeros((1, input_length, embedding_dim))

        num_tokens_to_take = min([input_length, len(tokens)])
        trimmed_tokens = tokens[:num_tokens_to_take]

        for j, token in enumerate(trimmed_tokens):
            # print(len(token.vector))
            text_features[0, j, :] = token.vector
        # Bringing to shape of (1, input_length * embedding_dim)
        ## ATTN - nlp vector:
        text_features = np.reshape(text_features, (1, input_length * embedding_dim))
    except Exception as ex:
        print(f'Failed to get embedding for {txt}')
        raise
    return text_features


def pre_process_raw_data(df):
    df['image_name'] = df['image_name'].apply(lambda q: q if q.lower().endswith('.jpg') else q + '.jpg')
    paths = df['path']

    dirs = {os.path.split(c)[0] for c in paths}
    files_by_folder = {dir: os.listdir(dir) for dir in dirs}
    existing_files = [os.path.join(dir, fn) for dir, fn_arr in files_by_folder.items() for fn in fn_arr]

    df = df.loc[df['path'].isin(existing_files)]

    # df = df[df['path'].isin(existing_files)]
    # df = df.where(df['path'].isin(existing_files))
    logger.debug('Getting answers embedding')
    # Note: Test has noanswer...
    df['answer_embedding'] = df['answer'].apply(lambda q: get_text_features(q) if isinstance(q, str) else "")

    logger.debug('Getting questions embedding')
    df['question_embedding'] = df['question'].apply(lambda q: get_text_features(q))

    logger.debug('Getting image features')
    df['image'] = df['path'].apply(lambda im_path: get_image(im_path))

    logger.debug('Done')
    return df


def normalize_data_strucrture(df, group, image_folder):
    # assert group in ['train', 'validation']
    cols = ['image_name', 'question', 'answer']

    df_c = df[cols].copy()
    df_c['group'] = group

    def get_image_path(image_name):
        return os.path.join(image_folder, image_name + '.jpg')

    df_c['path'] = df_c.apply(lambda x: get_image_path(x['image_name']),
                              axis=1)  # x: get_image_path(x['group'],x['image_name'])

    return df_c


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    from pre_processing.known_find_and_replace_items import find_and_replace_collection

    find_and_replace_data = find_and_replace_collection

    def replace_func(val: str) -> str:
        new_val = val
        if isinstance(new_val, str):
            for tpl in find_and_replace_data:
                pattern = re.compile(tpl.orig, re.IGNORECASE)
                new_val = pattern.sub(tpl.sub, new_val).strip()
        return new_val

    df['question'] = df['question'].apply(replace_func)
    df['answer'] = df['answer'].apply(replace_func)
    return df


def _consolidate_image_devices(df):
    def get_imaging_device(r):
        if r.ct and r.mri:
            res = 'both'
        elif r.ct and not r.mri:
            res = 'ct'
        elif not r.ct and r.mri:
            res = 'mri'
        else:
            res = 'unknown'
        return res

    df['imaging_device'] = df.apply(get_imaging_device, axis=1)

    imaging_device_by_image = defaultdict(lambda: set())
    for i, r in df.iterrows():
        imaging_device_by_image[r.image_name].add(r.imaging_device)

    for name, s in imaging_device_by_image.items():
        if 'both' in s or ('ct' in s and 'mri' in s):
            s.clear()
            s.add('unknown')
        elif 'unknown' in s and ('ct' in s or 'mri' in s):
            is_ct = 'ct' in s
            s.clear()
            s.add('ct' if is_ct else 'mri')

    non_consolidated_vals = [s for s in list(imaging_device_by_image.values()) if len(s) != 1]
    imaging_device_by_image = {k: list(s)[0] for k, s in imaging_device_by_image.items()}
    assert len(
        non_consolidated_vals) == 0, f'got {len(non_consolidated_vals)} non consolodated image devices. for example:\n{non_consolidated_vals[:5]}'
    df['imaging_device'] = df.apply(lambda r: imaging_device_by_image[r.image_name], axis=1)
    return df


def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    from pre_processing.known_find_and_replace_items import imaging_devices, diagnosis, locations

    # add_imaging_columns
    _add_columns_by_search(df, indicator_words=imaging_devices, search_columns=['question', 'answer'])
    # add_diagnostics_columns
    _add_columns_by_search(df, indicator_words=diagnosis, search_columns=['question', 'answer'])
    # add_locations_columns
    _add_columns_by_search(df, indicator_words=locations, search_columns=['question', 'answer'])

    _consolidate_image_devices(df)
    for col in imaging_devices:
        del df[col]
    return df


def _add_columns_by_search(df, indicator_words, search_columns):
    from common.utils import has_word
    for word in indicator_words:
        res = None
        for col in search_columns:
            curr_res = df[col].apply(lambda s: has_word(word, s))
            if res is None:
                res = curr_res
            res = res | curr_res
        if any(res):
            df[word] = res
        else:
            logger.warn("found no matching for '{0}'".format(word))


def _concat_row(df: pd.DataFrame, col: str):
    return np.concatenate(df[col], axis=0)


def get_features(df: pd.DataFrame):
    image_features = np.asarray([np.array(im) for im in df['image']])
    # np.concatenate(image_features['question_embedding'], axis=0).shape
    question_features = _concat_row(df, 'question_embedding')
    reshaped_q = np.array([a.reshape(a.shape + (1,)) for a in question_features])

    features = ([f for f in [reshaped_q, image_features]])

    return features


def sentences_to_hot_vector(sentences:pd.Series, words_df:pd.DataFrame)->iter:
    from sklearn.preprocessing import MultiLabelBinarizer
    classes = words_df.values
    splatted_answers = [ans.lower().split() for ans in sentences]
    clean_splitted_answers = [[w for w in arr if w in classes] for arr in splatted_answers]

    mlb = MultiLabelBinarizer(classes=classes.reshape(classes.shape[0]), sparse_output=False)
    mlb.fit(classes)

    print(f'Classes: {mlb.classes_}')
    arr_one_hot_vector = mlb.transform(clean_splitted_answers)
    return arr_one_hot_vector

def hot_vector_to_words(hot_vector, words_df):
    max_val = hot_vector.max()
    max_loc = np.argwhere(hot_vector == max_val)
    max_loc = max_loc.reshape(max_loc.shape[0])
    return words_df.iloc[max_loc]


def predict(model, df_data: pd.DataFrame, meta_data_location=None, percentile=99.8):
    # def apredict(model, df_data: pd.DataFrame, meta_data_location=None):

    # predict
    features = get_features(df_data)
    p = model.predict(features)

    percentiles = [np.percentile(curr_pred, percentile) for curr_pred in p]
    enumrated_p = [[(i, v) for i, v in enumerate(curr_p)] for curr_p in p]
    pass_vals = [([(i, curr_pred) for i, curr_pred in curr_pred_arr if curr_pred >= curr_percentile]) for
                 curr_pred_arr, curr_percentile in zip(enumrated_p, percentiles)]

    # [(i,len(curr_pass_arr)) for i, curr_pass_arr in  pass_vals]

    # vector-to-value
    predictions = [i for curr_pass_arr in pass_vals for i, curr_p in curr_pass_arr]
    results = [curr_p for curr_pass_arr in pass_vals for i, curr_p in curr_pass_arr]

    # dictionary for creating a data frame
    cols_to_transfer = ['image_name', 'question', 'answer', 'path']
    df_dict = {col_name: df_data[col_name] for col_name in cols_to_transfer}

    if meta_data_location:
        df_meta_words = pd.read_hdf(meta_data_location, 'words')
        results = df_meta_words.loc[predictions]

        imaging_device_probabilities = {row.word: [prediction[index] for prediction in p] for index, row in
                                        results.iterrows()}
        df_dict.update(imaging_device_probabilities)

    df_dict['prediction'] = " ".join([r for r in results.word.values])
    df = pd.DataFrame(df_dict)

    # Arranging in a prettier way
    sort_columns = ['image_name', 'question', 'answer', 'prediction']
    oredered_columns = sorted(df.columns, key=lambda v: v in sort_columns, reverse=True)
    df = df[oredered_columns]
    return df


def main():
    pass
    # print_function_code(get_nlp, remove_comments=True)


if __name__ == '__main__':
    main()
