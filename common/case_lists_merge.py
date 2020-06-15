import sys, os
from ruamel import yaml
import tempfile
import shutil

# Create tempfile version of files so that they can be modified for sample exclusions
# obj contains project_id and fpath
def return_tmpfiles_from_file_list(file_list):
    new_file_list = list()
    for i,f in enumerate(file_list):
        fname =  "tmp_file_" + str(i) +"_" + os.path.basename(f)
        tmp_dir = tempfile.gettempdir()
        temp_path = os.path.join(tmp_dir, fname)
        shutil.copy2(f, temp_path)
        new_file_list.append(temp_path)
    return new_file_list

# Need to replace tab characters with another delimiter so that the YAML parse works
def modify_files_to_remove_tabs(tmp_files):
    for f in tmp_files:
        with open(f, 'r') as my_file:
            data = my_file.readlines()
            for i,line in enumerate(data):
                line = line.replace(":\t",": ") #fixing inconsistent tab or space
                data[i] = line.replace("\t", ",")
        with open(f, 'w') as my_file:
            my_file.writelines( data )
    return tmp_files

def make_case_lists(file_list, study_id, case_type):
    tmp_files = return_tmpfiles_from_file_list(file_list)
    tmp_files = modify_files_to_remove_tabs(tmp_files)
    data = load_case_lists_files(tmp_files)
    case_data = get_values(data) 
    case_list_ids = get_case_list_ids(case_data)
    case_data['case_list_ids'] = case_list_ids
    case_data['cancer_study_identifier'] = study_id
    case_data['stable_id'] = study_id + "_" + case_type

    keys_to_join = ['case_list_name', 'case_list_description', 'case_list_category']
    # theoretically, these keys should only have one value after this join becaues they're in sets
    # and should have the same value across the different files

    for key in keys_to_join:
        case_data[key] = ";".join(case_data[key])

    return make_case_lists_string(case_data)

def make_case_lists_string(data):
    s = "case_list_category: %s\n" % data['case_list_category']
    s += "stable_id: %s\n" % data['stable_id']
    s += "case_list_name: %s\n" % data['case_list_name']
    s += "case_list_description: %s\n" % data['case_list_description']
    s += "cancer_study_identifier: %s\n" % data['cancer_study_identifier']
    s += "case_list_ids: %s\n" % data['case_list_ids']
    return s

def get_case_list_ids(data):
    unedited_ids = data['case_list_ids']
    id_set = set()
    for id_list in unedited_ids:
        ids = id_list.split(",")
        for i in ids:
            i = i.strip()
            id_set.add(i)
    return "\t".join(list(id_set))

def load_case_lists_files(file_list):
    case_data = list()
    for f in file_list:
        data = yaml.safe_load(open(f, 'r'))
        case_data.append(data)
    return case_data

def get_values(data_list):
    d = dict()
    for data in data_list:
        for key in data:
            if key not in d:
                d[key] = set()
            d[key].add(data[key])
    return d
