from collections import namedtuple
import os

# File Locations -------------------------------------------------------------
fn_meta            = os.path.abspath('./data/meta_data.json')
data_location      = os.path.abspath('./data/model_input.h5')
vqa_specs_location = os.path.abspath('./data/vqa_specs.pkl')

# The location to dump models to
vqa_models_folder  = "C:\\Users\\Public\\Documents\\Data\\2018\\vqa_models"

# -----------------------------------------------------------------------------

dbg_file_csv_train = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Train\\VQAMed2018Train-QA.csv'
dbg_file_xls_train = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Train\\VQAMed2018Train-QA_post_pre_process_intermediate.xlsx'#"'C:\\\\Users\\\\avitu\\\\Documents\\\\GitHub\\\\VQA-MED\\\\VQA-MED\\\\Cognitive-LUIS-Windows-master\\\\Sample\\\\VQA.Python\\\\dumped_data\\\\vqa_data.xlsx'
dbg_file_xls_processed_train = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Train\\VQAMed2018Train-QA_post_pre_process.xlsx'
train_embedding_path = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Train\\VQAMed2018Train-images\\embbeded_images.hdf'
images_path_train = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Train\\VQAMed2018Train-images'


dbg_file_csv_validation = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Valid\\VQAMed2018Valid-QA.csv'
dbg_file_xls_validation = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Valid\\VQAMed2018Valid-QA_post_pre_process_intermediate.xlsx'
dbg_file_xls_processed_validation = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Valid\\VQAMed2018Valid-QA_post_pre_process.xlsx'
validation_embedding_path = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Valid\\VQAMed2018Valid-images\\embbeded_images.hdf'
images_path_validation = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Valid\\VQAMed2018Valid-images'


dbg_file_csv_test = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Test\\VQAMed2018Test-QA.csv'
dbg_file_xls_test = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Test\\VQAMed2018Test-QA_post_pre_process_intermediate.xlsx'
dbg_file_xls_processed_test = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Test\\VQAMed2018Test-QA_post_pre_process.xlsx'
test_embedding_path = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Test\\VQAMed2018Test-images\\embbeded_images.hdf'
images_path_test = 'C:\\Users\\Public\\Documents\\Data\\2018\\VQAMed2018Test\\VQAMed2018Test-images'

DataLocations = namedtuple('DataLocations', ['data_tag', 'raw_csv', 'raw_xls', 'processed_xls','images_path'])
train_data = DataLocations('train', dbg_file_csv_train,dbg_file_xls_train,dbg_file_xls_processed_train, images_path_train)
validation_data = DataLocations('validation', dbg_file_csv_validation, dbg_file_xls_validation, dbg_file_xls_processed_validation, images_path_validation)
test_data = DataLocations('test', dbg_file_csv_test, dbg_file_xls_test, dbg_file_xls_processed_test, images_path_test)



