import os,sys
import pkgutil
import argparse
import pandas as pd
import glob

import common.clinical_data_merge as clin_data_merge
import common.clinical_meta_merge as clin_meta_merge
import common.case_lists_merge as case_lists_merge
import common.seg_merge as seg_merge
from typing import TypeVar
# Files to be merged
CLINICAL_DATA_PATIENT_FILE = "data_clinical_patient.txt"
CLINICAL_DATA_SAMPLE_FILE = "data_clinical_sample.txt"
DATA_CNA_FILE = "data_CNA.txt"
DATA_ASCNA_FILE = "data_CNA.ascna.txt"
DATA_FUSION_FILE = "data_fusions.txt"
DATA_SV_FILE = "data_sv.txt"
DATA_MUTATIONS_FILE = "data_mutations_extended.txt"
DATA_MUTATIONS_UNCALLED_FILE = "data_mutations_uncalled.txt"
CLINICAL_META_PATIENT_FILE = "meta_clinical_patient.txt" # might be unnecessary
CLINICAL_META_SAMPLE_FILE = "meta_clinical_sample.txt" # might be unnecessary
META_STUDY_FILE = "meta_study.txt"
CASE_LISTS_ALL = "case_lists/cases_all.txt"
CASE_LISTS_CNASEQ = "case_lists/cases_cnaseq.txt"
CASE_LISTS_CNA = "case_lists/cases_cna.txt"
CASE_LISTS_SEQ = "case_lists/cases_sequenced.txt"

class NonNoneSet(set):
    def add(self, element: TypeVar("_T")) -> None:
        if element != None:
            return super().add(element)


def add_file_to_merge(dirpath, fname):
    fpath = os.path.join(dirpath, fname)
    if os.path.exists(fpath):
        return fpath

def make_directory(path):
    try:
        if not os.path.exists(path):
            os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)

def get_file_from_glob(path):
    result = glob.glob(path)
    if len(result) > 1:
        print("Found multiple files when there should only be one: %s" % ";".join(result))
        sys.exit(1)
    if result:
        return result[0]

def write_dict(output_dir, d):
    for key in d:
        fname = os.path.basename(key)
        fpath = os.path.join(output_dir, fname)
        o = open(fpath, 'w')
        o.write(d[key])
        o.close()

def get_dir_list(dirs):
    dir_list = list()
    for i in dirs:
        dir_list.append(i)
    return dir_list

def runner(request_dict):
    dir_list = get_dir_list(request_dict['directories'])
    study_id = request_dict['study_id'] 
    project_desc = request_dict['project_desc']
    title = request_dict['project_title']
    output_dir = request_dict['output_directory']
    sample_data_clinical_files = request_dict['sample_data_clinical_files']

    make_directory(output_dir)

    # load common files into sets
    samp_files = NonNoneSet()
    patient_files = NonNoneSet()
    meta_study_files = NonNoneSet()
    data_sv_files = NonNoneSet()
    data_cna_files = NonNoneSet()
    data_ascna_files = NonNoneSet()
    data_fusions_files = NonNoneSet()
    data_mutations_files = NonNoneSet()
    data_mutations_uncalled_files = NonNoneSet()
    cases_all = NonNoneSet()
    cases_cnaseq = NonNoneSet()
    cases_cna = NonNoneSet()
    cases_seq = NonNoneSet()
    seg_data_files = NonNoneSet()
    seg_meta_files = NonNoneSet()

    for directory in dir_list:
        samp_files.add(add_file_to_merge(directory, CLINICAL_DATA_SAMPLE_FILE))
        patient_files.add(add_file_to_merge(directory, CLINICAL_DATA_PATIENT_FILE))
        meta_study_files.add(add_file_to_merge(directory, META_STUDY_FILE))
        data_cna_files.add(add_file_to_merge(directory, DATA_CNA_FILE))
        data_ascna_files.add(add_file_to_merge(directory, DATA_ASCNA_FILE))
        data_fusions_files.add(add_file_to_merge(directory, DATA_FUSION_FILE))
        data_sv_files.add(add_file_to_merge(directory, DATA_SV_FILE))
        data_mutations_files.add(add_file_to_merge(directory, DATA_MUTATIONS_FILE))
        data_mutations_uncalled_files.add(add_file_to_merge(directory, DATA_MUTATIONS_UNCALLED_FILE))
        cases_all.add(add_file_to_merge(directory,CASE_LISTS_ALL))
        cases_cnaseq.add(add_file_to_merge(directory,CASE_LISTS_CNASEQ))
        cases_cna.add(add_file_to_merge(directory,CASE_LISTS_CNA))
        cases_seq.add(add_file_to_merge(directory,CASE_LISTS_SEQ))
        seg_data_files.add(get_file_from_glob(os.path.join(directory, "*data*.seg")))
        seg_meta_files.add(get_file_from_glob(os.path.join(directory, "*meta*seg.txt")))

    ## Load the sample data clinical files and retrieve the extra sample and patient dataframes
    sample_df, patient_df = clin_data_merge.read_sample_data_clinical(sample_data_clinical_files)
    
    ## Begin clinical data file processing

    data_clinical_sample = clin_data_merge.run_merge(samp_files, additional_df=sample_df)
    data_clinical_patient = clin_data_merge.run_merge_patient(patient_files, additional_df=patient_df)
    data_cna = clin_data_merge.merge_cna_fusions(data_cna_files, fillna=True)
    data_ascna = clin_data_merge.merge_cna_fusions(data_ascna_files, fillna=True)
    data_fusions = clin_data_merge.merge_mutations(data_fusions_files)
    data_sv = clin_data_merge.merge_mutations(data_sv_files)
    data_mutations = clin_data_merge.merge_mutations(data_mutations_files, deduplicate=True)
    if data_mutations_uncalled_files:
        data_mutations_uncalled = clin_data_merge.merge_mutations(data_mutations_uncalled_files, deduplicate=True)
    else:
        data_mutations_uncalled = None

    # write out data_clinical_patient/sample, data_cna
    data_map_for_write = dict()
    data_map_for_write[CLINICAL_DATA_SAMPLE_FILE] = data_clinical_sample
    data_map_for_write[CLINICAL_DATA_PATIENT_FILE] = data_clinical_patient
    data_map_for_write[DATA_CNA_FILE] = data_cna
    data_map_for_write[DATA_FUSION_FILE] = data_fusions
    data_map_for_write[DATA_SV_FILE] = data_sv
    data_map_for_write[DATA_MUTATIONS_FILE] = data_mutations
    if data_mutations_uncalled:
        data_map_for_write[DATA_MUTATIONS_UNCALLED_FILE] = data_mutations_uncalled
    data_map_for_write[DATA_ASCNA_FILE] = data_ascna
    write_dict(output_dir, data_map_for_write)

    ## Begin meta file processing
    meta_clinical_patient = (clin_meta_merge.make_meta_clinical(study_id, "PATIENT_ATTRIBUTES"))
    meta_clinical_sample = (clin_meta_merge.make_meta_clinical(study_id, "SAMPLE_ATTRIBUTES"))

    data_clinical_sample_merged_file = os.path.join(output_dir, CLINICAL_DATA_SAMPLE_FILE)

    params = dict()
    params['study_id'] = study_id
    params['desc'] = project_desc
    params['title'] = title 
    params['clin_sample_file'] = data_clinical_sample_merged_file # unfortunately needed from merged data clinical sample file to resolve type_of_cancer
    meta_study = (clin_meta_merge.get_meta_study(meta_study_files, params))

    # write out meta_study, meta_clinical_patient/sample, other_meta
    meta = clin_meta_merge.make_meta_info(study_id)
    # Do not write meta_mutations_uncalled.txt if data_mutations_uncalled does not exist
    if not data_mutations_uncalled:
        meta.pop('meta_mutations_uncalled.txt',None)
    meta[META_STUDY_FILE] = meta_study
    meta[CLINICAL_META_PATIENT_FILE] = meta_clinical_patient
    meta[CLINICAL_META_SAMPLE_FILE] = meta_clinical_sample
    write_dict(output_dir, meta)

    ## Begin writing case list files
    cases_all_merged = (case_lists_merge.make_case_lists(cases_all, study_id, "all"))
    cases_cna_merged = (case_lists_merge.make_case_lists(cases_cna, study_id, "cna"))
    cases_cnaseq_merged = (case_lists_merge.make_case_lists(cases_cnaseq, study_id, "cnaseq"))
    cases_seq_merged = (case_lists_merge.make_case_lists(cases_seq, study_id, "sequenced"))

    # write out case files
    cases_path = os.path.join(output_dir, "case_lists")
    make_directory(cases_path)
    cases = dict()
    cases[CASE_LISTS_ALL] = cases_all_merged
    cases[CASE_LISTS_CNA] = cases_cna_merged
    cases[CASE_LISTS_CNASEQ] = cases_cnaseq_merged
    cases[CASE_LISTS_SEQ] = cases_seq_merged
    write_dict(cases_path, cases)

    ## Begin writing seg files
    seg_data_merged_file_name = study_id + "_data_cna_hg19.seg"
    seg_meta_merged_file_name = study_id + "_meta_cna_hg19_seg.txt"
    seg_data_merged_file = os.path.join(output_dir, seg_data_merged_file_name)
    seg_data = seg_merge.load_seg_data(seg_data_files)
    seg_meta = seg_merge.create_seg_meta(seg_meta_files, study_id, seg_data_merged_file_name)

    # write out seg file
    seg = dict()
    seg[seg_data_merged_file_name] = seg_data
    seg[seg_meta_merged_file_name] = seg_meta
    write_dict(output_dir, seg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directories", nargs="+", required=True, help="List of directories to merge")
    parser.add_argument("--project_desc", required=True, help="Project description")
    parser.add_argument("--project_title", required=False, help="Project Title")
    parser.add_argument("--sample_data_clinical_files", required=False, help="Sample Data Clinical Files", nargs="*")
    parser.add_argument("--study_id", required=True, help="Study ID")
    parser.add_argument("--output_directory", required=False, help="Location of output directory")
    args =  parser.parse_args()
    request_dict = vars(args)
    runner(request_dict)
