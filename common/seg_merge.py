import pandas as pd
from ruamel import yaml

def load_seg_data(file_list):
    dfs = list()
    for fname in file_list:
        df = pd.read_csv(fname, sep="\t", header = 0, comment = '#', index_col = 0, keep_default_na=False)
        if not df.empty:
            dfs.append(df)
    main_df = pd.concat(dfs, sort=False)
    s = main_df.to_csv(sep='\t')
    return s

def create_seg_meta(file_list, study_id, seg_data_file_name):
    data = load_meta(file_list)
    meta_data = get_values(data)
    keys_to_join = ['datatype', 'description', 'genetic_alteration_type', 'reference_genome_id']
    for key in keys_to_join:
        meta_data[key] = ";".join(meta_data[key])
    s = 'cancer_study_identifier: %s\n' % study_id
    s += 'data_filename: %s\n' % seg_data_file_name
    s += 'datatype: %s\n' % meta_data['datatype']
    s += 'description: %s\n' % meta_data['description']
    s += 'genetic_alteration_type: %s\n' % meta_data['genetic_alteration_type']
    s += 'reference_genome_id: %s\n' % meta_data['reference_genome_id']
    return s

def load_meta(file_list):
    meta_data = list()
    for f in file_list:
        data = yaml.safe_load(open(f, 'rb'))
        meta_data.append(data)
    return meta_data

def get_values(data_list):
    d = dict()
    for data in data_list:
        for key in data:
            if key not in d:
                d[key] = set()
            d[key].add(data[key])
    return d
