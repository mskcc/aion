# aion
# Creates merged cbioportal files from multiple projects

## Usage

Requires:
- python 2.7.x
- A YAML file (see `resources/example.yaml`)

##### Command:
```python cbioportal_merge.py -y <yaml file>```

##### Output:
A `portal/` directory with meta, data clinical, case list, and seg files
