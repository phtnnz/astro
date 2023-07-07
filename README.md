# Astro

Python scripts for creating N.I.N.A JSON sequences and targets, from object data in CSV format and N.I.N.A templates

## nina-create-sequence
Builds a complete N.I.N.A sequence for the observation night, using a base template (with empty Sequence Target Area) and a target template (repeated for every singl object), from a CSV list of targets exported by NEO Planner.

The directory NINA-Templates-IAS/ contains the necessary N.I.N.A templates.

Currently used for the M49, the IAS Remote Telescope

```
usage: nina-create-sequence [-h] [-v] [-T TARGET_TEMPLATE] [-S SEQUENCE_TEMPLATE] [-D DESTINATION_DIR] [-o OUTPUT] [-t] [-p] [-n] [-N]
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
                        output .json file, default NEO-YYYY-MM-DD
  -t, --targets-only    create separate targets only
  -p, --prefix-target   prefix all target names with YYYY-MM-DD NNN
  -n, --no-output       dry run, don't create output files
  -N, --add-number      add number of frames (nNNN) to target name

Version: 0.4 / 2023-07-03 / Martin Junius
```

## test-shutter-open
For Hakos remote observatories roll-off roof control only, tests whether the roof aka "shutter" is in state "open".

```
usage: test-shutter-open [-h] [-v]

Test Hakos shutter (roof) status: returns exit code 0 if open, else 1

options:
  -h, --help     show this help message and exit
  -v, --verbose  debug messages

Version 0.3 / 2023-07-03 / Martin Junius
```

## N.I.N.A External Script
Use the batch files/wrappers with full path in N.I.N.A's "External Script" instruction

```
"D:\Users\remote\Documents\Scripts\test-shutter-open.bat"
"D:\Users\remote\Documents\Scripts\nina-flag-ready.bat" "TARGET"
```