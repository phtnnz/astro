# Astro

Python scripts for creating N.I.N.A JSON sequences and targets, from object data in CSV format and N.I.N.A templates

(See the most recent working* branch for bleeding edge code)

## nina-create-sequence
Builds a complete N.I.N.A sequence for the observation night, using a base template (with empty Sequence Target Area) and a target template (repeated for every single object), from a CSV list of targets exported by NEO Planner.

The directory NINA-Templates-IAS/ contains the necessary N.I.N.A templates.

Currently used for the M49, the IAS Remote Telescope

```
usage: nina-create-sequence [-h] [-v] [-T TARGET_TEMPLATE] [-S SEQUENCE_TEMPLATE] [-D DESTINATION_DIR] [-o OUTPUT] [-t] [-p] [-n] [-N] filename [filename ...]

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

Version: 1.0 / 2023-07-05 / Martin Junius
```

## test-shutter-open
For Hakos remote observatories roll-off roof control only, tests whether the roof aka "shutter" is in state "open".

```
usage: test-shutter-open [-h] [-v]

Test Hakos shutter (roof) status: returns exit code 0, if open, else 1

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

## astro-countsubs
Count sub frames in directory structure and compute total exposure time. Relies on YYYY-MM-DD sub-directories and FITS filenames containing filter name and exposure time.

```
usage: astro-countsubs [-h] [-v] [-x EXCLUDE] [-f FILTER] dirname

Traverse directory and count N.I.N.A subs

positional arguments:
  dirname               directory name

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -x EXCLUDE, --exclude EXCLUDE
                        exclude filter, e.g. Ha,SII
  -f FILTER, --filter FILTER
                        filter list, e.g. L,R,G.B

Version: 0.1 / 2023-07-07 / Martin Junius
```

## nina-zip-ready-data
Automatically archive N.I.N.A exposure when a target sequence has been completed,
relying on the .ready flags created by nina-flag-ready.bat run as an External Script
from within N.I.N.A
- Search TARGET.ready files in DATADIR
- Look for corresponding TARGET.7z archive in ZIPDIR
- If exists, skip
- If not, run 7z.exe to archive TARGET data subdir in DATA to TARGET.7z in ZIPDIR
- Loop continuously

```
usage: nina-zip-ready-data [-h] [-v] [-D DATA_DIR] [-Z ZIP_DIR] [-t TIME_INTERVAL] [-z ZIP_PROG]

Zip target data in N.I.N.A data directory marked as ready

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -D DATA_DIR, --data-dir DATA_DIR
                        N.I.N.A data directory (default D:/Users/remote/Documents/NINA-Data)
  -Z ZIP_DIR, --zip-dir ZIP_DIR
                        directory for zip (.7z) files (default C:/Users/remote/OneDrive/Remote-Upload)
  -t TIME_INTERVAL, --time-interval TIME_INTERVAL
                        time interval for checking data directory (default 60s)
  -z ZIP_PROG, --zip-prog ZIP_PROG
                        full path of 7-zip.exe (default C:/Program Files/7-Zip/7z.exe)

Version 0.1 / 2023-07-08 / Martin Junius
```