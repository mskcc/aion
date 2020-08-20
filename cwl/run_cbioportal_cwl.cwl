#!/usr/bin/env cwl-runner

class: CommandLineTool
cwlVersion: v1.0
doc: "
CWL for merging portal files from Argos projects

Inputs
------

The following parameters are required:
directories: a list of directory paths containing portal files
project_desc: A description of some kind for the 
study_id: string, should be set_<labHeadEmail without @*>

Optional parameters:

project_title: Optional, can be null
output_directory: By default, outputs to current working directory

Output
------

A folder containing merged txt files.
"

requirements:
  ScatterFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}
  SubworkflowFeatureRequirement: {}
  DockerRequirement:
    dockerPull: mskcc/aion:1.0.0

baseCommand: [ 'python3', '/usr/bin/aion/cbioportal_merge.py' ]

inputs:
  directories:
    type:
        type: array
        items: Directory
    inputBinding:
        prefix: --directories
    doc: "Contains a list of file paths"
  project_desc:
    type: string
    inputBinding:
        prefix: --project_desc
    doc: "Project description"
  project_title:
    type: string?
    inputBinding:
        prefix: --project_title
    doc: "Project title"
  study_id:
    type: string
    inputBinding:
        prefix: --study_id
    doc: "The study ID"
  output_directory:
    type: string
    default: "."
    inputBinding:
        prefix: --output_directory
    doc: "Path to the output directory, where to write merged files"

outputs:
  merged_directory:
    type: Directory
    outputBinding:
        glob: | 
            ${
                return inputs.output_directory;
            }
