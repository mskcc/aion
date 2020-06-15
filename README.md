# aion
# Creates merged cbioportal files from multiple projects

## Usage

Requires:
- python 3.x

##### Command:
```
usage: cbioportal_merge.py [-h] --directory DIRECTORY [DIRECTORY ...]
                           --project_desc PROJECT_DESC
                           [--project_title PROJECT_TITLE] --study_id STUDY_ID
                           [--output_directory OUTPUT_DIRECTORY]
```
##### Output:
A `portal/` directory with meta, data clinical, case list, and seg files
