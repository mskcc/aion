import sys
import pandas as pd
import pkgutil
from ruamel import yaml
from itertools import islice

from lib.oncotree_data_handler.OncotreeDataHandler import OncotreeDataHandler

def make_meta_clinical(study_id, datatype):
    s = "cancer_study_identifier: %s\n" % study_id
    s += "genetic_alteration_type: CLINICAL\n"
    s += "datatype: %s\n" % datatype
    if datatype == "SAMPLE_ATTRIBUTES":
        s += "data_filename: data_clinical_sample.txt"+ '\n'
        return s
    s += "data_filename: data_clinical_patient.txt" + '\n'
    return s

# Since CNA, fusions, and mutations_extended are assumed stable, this returns a dictionary
#   with what's supposed to be written into each respective file.
#
# The keys of the dictionary are the output file names
def make_meta_info(study_id):
    meta_vars = dict()
    meta_vars['meta_CNA.txt'] = { 'study_id': study_id,
            'fname': 'data_CNA.txt',
            'datatype': 'DISCRETE',
            'alteration_type': 'COPY_NUMBER_ALTERATION',
            'desc': 'Discrete Copy Number Data',
            'name': 'Discrete Copy Number Data',
            'show': 'true',
            'stable_id': 'cna' }

    meta_vars['meta_fusions.txt'] = { 'study_id': study_id,
            'fname': 'data_fusions.txt', 'datatype': 'FUSION',
            'alteration_type': 'FUSION',
            'desc': 'Fusion data',
            'name': 'Fusions',
            'show': 'true',
            'stable_id': 'fusion' }

    meta_vars['meta_mutations_extended.txt'] = { 'study_id': study_id,
            'fname': 'data_mutations_extended.txt',
            'datatype': 'MAF',
            'alteration_type': 'MUTATION_EXTENDED',
            'desc': 'Mutation data',
            'name': 'Mutations',
            'show': 'true',
            'stable_id': 'mutations' }

    data = make_meta_files(meta_vars)
    return data

# only for cna, fusions, and extended mutations at the moment
def make_meta_files(meta_vars):
    results = dict() 
    for key in meta_vars:
        var = meta_vars[key]
        s = "cancer_study_identifier: %s\n" % var['study_id']
        s += "data_filename: %s\n" % var['fname']
        s += "datatype: %s\n" % var['datatype']
        s += "genetic_alteration_type: %s\n" % var['alteration_type']
        s += "profile_description: %s\n" % var['desc']
        s += "profile_name: %s\n" % var['name']
        s += "show_profile_in_analysis_tab: %s\n" % var['show']
        s += "stable_id: %s\n" % var['stable_id']
        results[key] = s
    return results

# params keys: study_id, title, clin_sample_file, desc
# Should clean this up later but this is only for meta_study.txt
def get_meta_study(file_list, params):
    data = load_meta_files(file_list)
    merged_meta = get_values(data)
    # overwrite with params values
    if params['title'] is not None:
        merged_meta['name'] = params['title']
    else:
        meta_title = ";".join(list(merged_meta['name']))[:255] # cbioportal title character limit 
        merged_meta['name'] = meta_title

    merged_meta['cancer_study_identifier'] = params['study_id']
    merged_meta['short_name'] = params['study_id']
    if params['desc'] is not None:
        merged_meta['description'] = params['desc']
    else:
        meta_desc =  ";".join(list(merged_meta['description']))
        merged_meta['description'] = meta_desc[:1000] # cbioportal character limit

    # combine groups
    merged_meta['groups'] = ";".join(list(merged_meta['groups']))

    # write output string
    df = pd.read_csv(params['clin_sample_file'], comment="#", sep="\t", keep_default_na=False, converters={'PROJECT_ID': lambda x: str(x)})
    df.fillna('', inplace=True)
    cancer_type = get_onco_code(df)
    s = "cancer_study_identifier: %s\n" % merged_meta['cancer_study_identifier']
    s += "description: %s\n" % merged_meta['description'] 
    s += "name: %s\n" % merged_meta['name']
    s += "groups: %s\n" % merged_meta['groups']
    s += "short_name: %s\n" % merged_meta['short_name']
    s += "type_of_cancer: %s\n" % cancer_type
    return s

def get_values(data_list):
    d = dict()
    for data in data_list:
        for key in data:
            if key not in d:
                d[key] = set()
            d[key].add(data[key])
    return d

def load_meta_files(file_list):
    meta_data = list()
    for f in file_list:
        data = yaml.safe_load(open(f, 'rb'))
        meta_data.append(data)
    return meta_data

def get_onco_code(df):
    oncotree_dh = OncotreeDataHandler()
    code_list = df['ONCOTREE_CODE'].values.tolist()

    shared_nodes = oncotree_dh.find_shared_nodes_by_code_list(code_list)
    common_anc = oncotree_dh.get_highest_level_shared_node(shared_nodes)
    if common_anc.code.lower() == "tissue":
        return 'mixed'
    return common_anc.code.lower()
