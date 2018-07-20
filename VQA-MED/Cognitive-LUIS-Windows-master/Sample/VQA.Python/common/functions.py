import inspect
import os
import re

import pandas as pd
import cv2
import numpy as np

from common.settings import input_length, image_size, get_nlp
from common.settings import  embedding_dim
from vqa_logger import logger


def get_size(file_name):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    nbytes = os.path.getsize(file_name)
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
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
    files_by_folder = {dir:os.listdir(dir) for dir in dirs }
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
        return os.path.join(image_folder, image_name+ '.jpg')

    df_c['path'] = df_c.apply(lambda x:  get_image_path(x['image_name']),axis=1) #x: get_image_path(x['group'],x['image_name'])

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


def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    from pre_processing.known_find_and_replace_items import imaging_devices, diagnosis, locations

    # add_imaging_columns
    _add_columns_by_search(df, indicator_words=imaging_devices, search_columns=['question', 'answer'])
    # add_diagnostics_columns
    _add_columns_by_search(df, indicator_words=diagnosis, search_columns=['question', 'answer'])
    # add_locations_columns
    _add_columns_by_search(df, indicator_words=locations, search_columns=['question', 'answer'])
    return df





def _add_columns_by_search(df, indicator_words, search_columns):
    from common.utils import has_word
    for word in indicator_words:
        res = None
        for col in search_columns:
            curr_res = df[col].apply(lambda s: has_word(word,s))
            if res is None:
                res = curr_res
            res = res | curr_res
        if any(res):
            df[word] = res
        else:
            logger.warn("found no matching for '{0}'".format(word))

def main():
    pass
    # print_function_code(get_nlp, remove_comments=True)

if __name__ == '__main__':
    main()