import sys
import pandas as pd
import pkgutil
from ruamel import yaml
from itertools import islice

# Expects clinical data files to have first four lines to have # as first char (required by cbioportal)
# But the FIFTH line contains the actual header values
# See Data files section in https://github.com/cBioPortal/cbioportal/blob/master/docs/File-Formats.md#clinical-data

ROW_HEADER = 4
ROW_DISPLAY = 0
ROW_DESC = 1
ROW_DATATYPE = 2
ROW_PRIORITY = 3

COL_SAMPLES_ORDER = ["SAMPLE_ID", "PATIENT_ID"]
DATA_MUTATIONS_UNIQ_COLS = ["Chromosome","Start_Position","End_Position","Reference_Allele","Tumor_Seq_Allele2","Tumor_Sample_Barcode"]
DEFINITIONS_CLINICAL = yaml.safe_load(pkgutil.get_data('cbioportal_merge', 'resources/clinical_data/data.yaml'))
COL_PATIENT = ["PATIENT_ID","SEX"]
COL_SAMPLE = [col for col in DEFINITIONS_CLINICAL.keys() if col != "SEX"]

def run_merge(file_list, additional_df=None):
    clinical_attrs_by_file = get_clinical_attrs(file_list)
    clin_attrs = get_union_attrs(clinical_attrs_by_file)
    combined_df = combine_files(file_list, additional_df=additional_df)
    header = create_portal_header(clin_attrs, combined_df)
    data = create_data_rows(combined_df)
    output_string = header + data
    return output_string

def run_merge_patient(file_list, additional_df=None):
    clinical_attrs_by_file = get_clinical_attrs(file_list)
    clin_attrs = get_union_attrs(clinical_attrs_by_file)
    combined_df = combine_files_patient(file_list, additional_df=additional_df)
    header = create_portal_header(clin_attrs, combined_df)
    data = create_data_rows(combined_df)
    output_string = header + data
    return output_string

def create_portal_header(clin_attrs, df):
    header_order = df.columns
    display_names = [] 
    desc = []
    datatype = [] 
    priority = [] 

    for col in header_order:
        display_names.append(get_value(clin_attrs[col]['display_name']))
        desc.append(get_value(clin_attrs[col]['desc']))
        datatype.append(get_value(clin_attrs[col]['datatype']))
        priority.append(get_value(clin_attrs[col]['priority']))

    header = "#" + "\t".join(display_names) + "\n"
    header += "#" + "\t".join(desc) + "\n"
    header += "#" + "\t".join(datatype) + "\n"
    header += "#" + "\t".join(priority) + "\n"
    return header

def create_data_rows(df):
    s = "\t".join(df.columns.values.tolist()) + "\n"# just adding the header from the dataframe
    data = df.values.tolist()
    for i in data:
        val = map(str, i)
        s += "\t".join(val) + "\n"
    return s

def get_value(val):
    if isinstance(val, int):
        return str(val)
    return val

def combine_files(file_list, additional_df=pd.DataFrame()):
    dfs = list()
    for fname in file_list:
        df = pd.read_csv(fname, index_col = None, sep="\t", header = 0, comment = '#', keep_default_na=False, converters={'PROJECT_ID': lambda x: str(x), 'REQUEST_ID': lambda x: str(x)})
        df.fillna('', inplace=True)
        dfs.append(df)
    if not additional_df.empty:
        dfs.append(additional_df)
    return pd.concat(dfs,ignore_index=True).drop_duplicates(subset='SAMPLE_ID').reset_index(drop=True)

def combine_files_patient(file_list, additional_df=pd.DataFrame()):
    dfs = list()
    for fname in file_list:
        df = pd.read_csv(fname, index_col = None, sep="\t", header = 0, comment = '#', keep_default_na=False)
        df.fillna('', inplace=True)
        dfs.append(df)
    if not additional_df.empty:
        dfs.append(additional_df)
    return pd.concat(dfs,ignore_index=True).drop_duplicates(subset='PATIENT_ID').reset_index(drop=True)

def read_sample_data_clinical(file_list):
    sample_dfs = list()
    patient_dfs = list()
    dedup_sample_df = None
    dedup_patient_df = None
    for fname in file_list:
        sample_data_df = pd.read_csv(fname, index_col = None, sep="\t", header = 0, comment = '#', keep_default_na=False)
        sample_data_df.fillna('', inplace=True)
        sample_df = pd.DataFrame(sample_data_df, columns=[col for col in sample_data_df if col in  COL_SAMPLE])
        patient_df = pd.DataFrame(sample_data_df, columns=[col for col in sample_data_df if col in  COL_PATIENT])
        sample_dfs.append(sample_df)
        patient_dfs.append(patient_df)
    dedup_sample_df = pd.concat(sample_dfs,ignore_index=True).drop_duplicates(subset='SAMPLE_ID').reset_index(drop=True)
    dedup_patient_df = pd.concat(patient_dfs,ignore_index=True).drop_duplicates(subset='PATIENT_ID').reset_index(drop=True)
    return dedup_sample_df, dedup_patient_df

def create_col_order(attrs):
    col_order = list()
    if "SAMPLE_ID" in attrs:
        col_order = COL_SAMPLES_ORDER
    for key in attrs:
        if key not in col_order:
            col_order.append(key)     
    return col_order

# Get a master dictionary filled with all attributes found from all files
def get_union_attrs(clinical_attrs_by_file):
    union_attrs = dict()
    for file_name in clinical_attrs_by_file:
        clin_attrs = clinical_attrs_by_file[file_name]
        for key in clin_attrs:
            if key not in union_attrs:
                union_attrs[key] = clin_attrs[key]
    union_attrs = override_attr(union_attrs, DEFINITIONS_CLINICAL)
    check_attr(union_attrs, DEFINITIONS_CLINICAL)
    return union_attrs

# Gets the attributes from clinical data files.
def get_clinical_attrs(file_list):
    # get expected header attributes from YAML files
    clinical_attrs = dict()
    for clin_file in file_list:
        attrs = get_attr(clin_file)
        clinical_attrs[clin_file] = attrs
    return clinical_attrs

def override_attr(attrs, attr_override):
    for key in attrs:
        if key in attr_override:
            attrs[key] = attr_override[key]
    return attrs

def check_attr(attrs, expected_attrs):
    for key in expected_attrs:
        if key in attrs:
            for attr in expected_attrs[key]:
                expected = expected_attrs[key][attr]
                actual = attrs[key][attr]
                if actual != expected:
                    print("Data does not match:")
                    print("\tExpected Key %s, attribute %s, expected value %s" % (key, attr, expected))
                    print("\tActual Key %s, attribute %s, actual value %s" % (key, attr, actual))
                    sys.exit(1)

def get_attr(clin_file):
    with open(clin_file, 'r') as f:
        data = list(islice(f, 5))
    headers = data[ROW_HEADER].strip().split("\t")
    attrs = compile_attrs(headers, data)
    return attrs

def compile_attrs(headers,data):
    d = dict()
    for i,header in enumerate(headers):
        if header not in d:
            d[header] = dict()
        d[header]["display_name"] = match_headers_with_data(i, data[ROW_DISPLAY])
        d[header]['desc'] = match_headers_with_data(i, data[ROW_DESC])
        d[header]['datatype'] = match_headers_with_data(i, data[ROW_DATATYPE])
        d[header]['priority'] = match_headers_with_data(i, data[ROW_PRIORITY])
    return d

def match_headers_with_data(header_index, data):
    line = data.strip().split("\t")
    try:
        return format_string(line[header_index])
    except:
        print("An error has occurred during header match")
        print("Likely the formatting of the files being merged is unexpected; check data files.")

def format_string(s):
    if s[0] == '#':
        s = s[1:]
    return str(s)

# We are asuming file_list will always be non-empty
def return_only_header(file_list):
    header = ""
    f = file_list.pop()
    data = pd.read_csv(f, sep="\t", header = 0, comment = '#', index_col = 0, keep_default_na=False)
    return "\t".join(data.columns) + "\n"

def merge_cna_fusions(file_list, fillna=False):
    dfs = list()
    try:
        for fname in file_list:
            df = pd.read_csv(fname, sep="\t", header = 0, comment = '#', index_col = 0, keep_default_na=False)
            if not df.empty:
                dfs.append(df) 
        main_df = pd.concat(dfs, axis=1, sort=False)
        if fillna:
            main_df = main_df.fillna("NA")
        main_df.index.name = 'Hugo_Symbol'
        s = main_df.to_csv(sep='\t')
    except ValueError:
        s = ""
        print("No fusion files to concatenate")
    return s

def merge_mutations(file_list, fillna=False, deduplicate=False):
    dfs = list()
    try:
        for fname in file_list:
            df = pd.read_csv(fname, sep="\t", header = 0, comment = '#', index_col = 0, keep_default_na=False)
            df.reset_index()
            if not df.empty:
                dfs.append(df) 
        main_df = pd.concat(dfs, sort=False)
        if fillna:
            main_df = main_df.fillna("NA")
        if deduplicate:
            main_df.drop_duplicates(subset=DATA_MUTATIONS_UNIQ_COLS)
        s = main_df.to_csv(sep='\t')
    except ValueError:
        s = return_only_header(file_list)
        print("No mutation files to concatenate; returning only header")
    return s

# Need to get header for files so that they can be merged
def get_columns_from_files(file_list):
    columns = set()
    for fname in file_list:
        df = pd.read_csv(fname, index_col = None, sep="\t", header = 0, comment = '#', keep_default_na=False)
        cols = df.columns.values.tolist()
        for i in cols:
            columns.add(i)
    return columns

def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
