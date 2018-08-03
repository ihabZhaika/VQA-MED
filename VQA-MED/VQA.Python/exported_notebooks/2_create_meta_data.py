
# coding: utf-8

# In[1]:


import os
import pandas as pd
from pandas import HDFStore


# In[2]:


# Pre process results files
fn_meta            = os.path.abspath('data/meta_data.json')


# In[3]:


from common.constatns import data_location, vqa_specs_location
from common.settings import embedding_dim, seq_length
from common.classes import VqaSpecs


# ### Preprocessing and creating meta data

# Get the data itself, Note the only things required in dataframe are:
# 1. image_name
# 2. question
# 3. answer
# 

# In[4]:


print(f'loading from:\n{data_location}')
with HDFStore(data_location) as store:
     df_data = store['data']
        
df_data = df_data[df_data.group.isin(['train','validation'])]
print(f'Data length: {len(df_data)}')        
df_data.head()


# #### We will use this function for creating meta data:

# In[5]:


from vqa_logger import logger 
import itertools
import string
from common.os_utils import File #This is a simplehelper file of mine...

def create_meta(df):
        
        print(f"Dataframe had {len(df)} rows")
        def get_unique_words(col):
            single_string = " ".join(df[col])
            exclude = set(string.punctuation)
            s_no_panctuation = ''.join(ch for ch in single_string if ch not in exclude)
            unique_words = set(s_no_panctuation.split(" ")).difference({'',' '})
            print("column {0} had {1} unique words".format(col,len(unique_words)))
            return unique_words

        cols = ['question', 'answer']
        df_unique_words = set(itertools.chain.from_iterable([get_unique_words(col) for col in cols]))
        df_unique_answers = set(df['answer'])        
        
        df_unique_imaging_devices = set(df['imaging_device'])        

        metadata = {}
        metadata['ix_to_word'] = {str(word): int(i) for i, word in enumerate(df_unique_words)}
        metadata['ix_to_ans'] = {i:ans for i, ans in enumerate(df_unique_answers)}
        metadata['ans_to_ix'] = {ans:i for i, ans in enumerate(df_unique_answers)}
        
        metadata['img_device_to_ix'] = {ans:i for i, ans in enumerate(df_unique_imaging_devices)}
        metadata['ix_to_img_device'] = {i:ans for i, ans in enumerate(df_unique_imaging_devices)}
                
        
        #------------------- Asserts
        answers = metadata['ix_to_ans'].values()
        words = metadata['ix_to_word'].values()
        
        assert len(set(answers)) == len(answers), 'Got duplicate answers'
        assert len(set(words)) == len(words), 'Got duplicate words'        
        #---------------------------
        
        print("Meta number of unique answers: {0}".format(len(set(metadata['ix_to_ans'].values()))))
        print("Meta number of unique words: {0}".format(len(set(metadata['ix_to_word'].values()))))

       
        return metadata


# In[6]:


print("----- Creating meta -----")
meta_data = create_meta(df_data)

# pd.DataFrame(meta_data).head()
meta_data.keys()


# In[7]:


File.dump_json(meta_data,fn_meta)
print(f"Meta file available at: {fn_meta}")


# #### Saving the data, so later on we don't need to compute it again

# In[8]:


def get_vqa_specs(meta_data):    
    dim = embedding_dim
    s_length = seq_length    
    return VqaSpecs(embedding_dim=dim, seq_length=s_length, data_location=data_location,meta_data=meta_data)

vqa_specs = get_vqa_specs(meta_data)

# Show waht we got...
s = str(vqa_specs)
s[:s.index('meta_data=')+10]


# In[9]:


File.dump_pickle(vqa_specs, vqa_specs_location)
logger.debug(f"VQA Specs saved to:\n{vqa_specs_location}")


# In[10]:


print (f"vqa_specs_location = '{vqa_specs_location}'".replace('\\','\\\\'))
