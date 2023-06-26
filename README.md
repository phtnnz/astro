# astro

Python scripts for creating N.I.N.A JSON sequences and targets, from object data in CSV format and N.I.N.A templates


```
usage: nina-create-sequence [-h] [-v] [-T TARGET_TEMPLATE] [-S SEQUENCE_TEMPLATE] [-D DESTINATION_DIR] [-o OUTPUT] [-l LEVEL] [-t] [-p] [-n]
                            filename [filename ...]

Create/populate multiple N.I.N.A target templates/complete sequence with data from NEO Planner CSV

positional arguments:
  filename              CSV target data list

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -T TARGET_TEMPLATE, --target-template TARGET_TEMPLATE
                        base N.I.N.A target template .json file
  -S SEQUENCE_TEMPLATE, --sequence-template SEQUENCE_TEMPLATE
                        base N.I.N.A sequence .json file
  -D DESTINATION_DIR, --destination-dir DESTINATION_DIR
                        output dir for created targets/sequence
  -o OUTPUT, --output OUTPUT
                        output .json file, default NEW-YYYY-MM-DD
  -l LEVEL, --level LEVEL
                        limit recursion depth
  -t, --targets-only    create separate targets only
  -p, --prefix-target   prefix all target names with YYYY-MM-DD NNN
  -n, --no-output       dry run, don't create output files

Version: 0.1 / 2023-06-24 / Martin Junius
´´´
