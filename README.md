# Astro

Python scripts for creating N.I.N.A JSON sequences and targets, from object data in CSV format and N.I.N.A templates

Copyright 2023 Martin Junius

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


(See the most recent working* branch for bleeding edge code)

The following additional Python libraries must be installed:

| Library  | PyPI URL                           |
| -------- | ---------------------------------- |
| requests | https://pypi.org/project/requests/ |
| psutil   | https://pypi.org/project/psutil/   |
| icecream | https://pypi.org/project/icecream/ |

Local modules:

| Library          | Function                           |
| ---------------- | ---------------------------------- |
| mpc.mpcdata80    | Class for handling MPC 80-column data format |
| mpc.mpcosarchive | Class for handling MPC/MPO/MPS archive |
| mpc.verbose      | verbose(), warning() and error() messages, mpc modules copy |
| jsonconfig       | Read/write JSON config files for the astro scripts |
| verbose          | verbose(), warning() and error() messages |


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
For Hakos remote observatories roll-off roof control only, checks roof/mount status.

```
usage: test-shutter-open [-h] [-v] [-P] [-O]

Test Hakos roof (shutter) status: returns exit code 0, if ok (open/parked), else 1

options:
  -h, --help     show this help message and exit
  -v, --verbose  debug messages
  -P, --parked   test for "parked" status
  -O, --open     test for "open" status (default)

Version 0.4 / 2024-06-20 / Martin Junius
```

## test-hakos-roof
For Hakos remote observatories roll-off roof control only, refactored status queries

```
usage: test-hakos-roof [-h] [-v] [-d] [-P] [-O]

Test Hakos roof (shutter) status: returns exit code 0, if ok (open/parked), else 1

options:
  -h, --help     show this help message and exit
  -v, --verbose  debug messages
  -d, --debug    more debug messages
  -P, --parked   test for "parked" status
  -O, --open     test for "open" status (default)

Version 1.0 / 2024-06-20 / Martin Junius
```


## N.I.N.A External Script
Use the batch files/wrappers with full path in N.I.N.A's "External Script" instruction

```
"D:\Users\remote\Documents\Scripts\test-shutter-open.bat"
"D:\Users\remote\Documents\Scripts\test-hakos-roof.bat"
"D:\Users\remote\Documents\Scripts\nina-flag-ready.bat" "TARGET"
```


## astro-countsubs
Count sub frames in directory structure and compute total exposure time. Relies on YYYY-MM-DD sub-directories and FITS filenames containing filter name and exposure time. Additional data on calibration from JSON config file.

```
usage: astro-countsubs [-h] [-v] [-d] [-x EXCLUDE] [-f FILTER] [-t EXPOSURE_TIME] [-C] [-o OUTPUT] [-F FILTER_SET] [--calibration-set CALIBRATION_SET] dirname

Traverse directory and count N.I.N.A subs

positional arguments:
  dirname               directory name

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -d, --debug           more debug messages
  -x EXCLUDE, --exclude EXCLUDE
                        exclude filter, e.g. Ha,SII
  -f FILTER, --filter FILTER
                        filter list, e.g. L,R,G.B
  -t EXPOSURE_TIME, --exposure-time EXPOSURE_TIME
                        exposure time (sec) if not present in filename
  -C, --csv             output CSV list
  -o OUTPUT, --output OUTPUT
                        write to file OUTPUT
  -F FILTER_SET, --filter-set FILTER_SET
                        name of filter set for Astrobin CSV (see config)
  --calibration-set CALIBRATION_SET
                        name of calibration set

Version: 0.5 / 2024-06-18 / Martin Junius
```

JSON config file astro-countsubs-config.json

Examples:

```
astro-countsubs.py --filter-set "Astronomik 2in" --calibration-set ak3-asi294mc-2024 --filter L '\Images\NGC 6744\'
```
OSC with just an Astronomik L-2 filter, text output

```
astro-countsubs.py --filter-set "Baader 36mm" --calibration-set remote3 --csv -o tmp/NGC5139.csv '\Images\NGC 5139\'
```
Mono camera with Baader filter set, output CSV file for Astrobin import


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
usage: nina-zip-ready-data [-h] [-v] [-l] [-D DATA_DIR] [-Z ZIP_DIR] [-t TIME_INTERVAL] [-z ZIP_PROG]

Zip target data in N.I.N.A data directory marked as ready

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -l, --low-priority    set process priority to low
  -D DATA_DIR, --data-dir DATA_DIR
                        N.I.N.A data directory (default D:/Users/remote/Documents/NINA-Data)
  -Z ZIP_DIR, --zip-dir ZIP_DIR
                        directory for zip (.7z) files (default C:/Users/remote/OneDrive/Remote-Upload)
  -t TIME_INTERVAL, --time-interval TIME_INTERVAL
                        time interval for checking data directory (default 60s)
  -z ZIP_PROG, --zip-prog ZIP_PROG
                        full path of 7-zip.exe (default C:/Program Files/7-Zip/7z.exe)

Version 0.2 / 2023-07-09 / Martin Junius
```

## nina-zip-last-night
Archive all N.I.N.A data from the last observation night (or date given by the -d option)
- Search all TARGET/YYYY-MM-DD directories in DATADIR
- Look for corresponding TARGET-YYYY-MM-DD.7z archive in ZIPDIR
- If exists, skip
- If not, run 7z.exe to archive TARGET/YYYY-MM-DD data subdir in DATA to TARGET-YYYY-MM-DD.7z in ZIPDIR

```
usage: nina-zip-last-night [-h] [-v] [-d] [-n] [-l] [--date DATE] [-t TARGETS] [-D DATA_DIR] [-Z ZIP_DIR] [-z ZIP_PROG] [-m]

Zip target data in N.I.N.A data directory from last night

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -d, --debug           more debug messages
  -n, --no-action       dry run
  -l, --low-priority    set process priority to low
  --date DATE           archive target/DATE, default last night 2024-06-25
  -t TARGETS, --targets TARGETS
                        archive TARGET[,TARGET] only
  -D DATA_DIR, --data-dir DATA_DIR
                        N.I.N.A data directory (default D:/Users/remote/Documents/NINA-Data)
  -Z ZIP_DIR, --zip-dir ZIP_DIR
                        directory for zip (.7z) files (default C:/Users/remote/OneDrive/Remote-Upload)
  -z ZIP_PROG, --zip-prog ZIP_PROG
                        full path of 7-zip.exe (default C:/Program Files/7-Zip/7z.exe)
  -m, --zip_max         7-zip max compression -mx7

Version 0.2 / 2024-05-01 / Martin Junius
```


## mpc-retrieve-ack
Retrieve Minor Planets Center observation data from IMAP server with ACK mails, and MPC WAMO service

```
usage: mpc-retrieve-ack [-h] [-v] [-d] [-n] [-l] [-f IMAP_FOLDER] [-L] [-m MSGS] [-o OUTPUT] [-C] [-O] [-D]

Retrieve MPC ACK mails

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose messages
  -d, --debug           more debug messages
  -n, --no-wamo-requests
                        don't request observations from minorplanetcenter.net WAMO
  -l, --list-folders-only
                        list folders on IMAP server only
  -f IMAP_FOLDER, --imap-folder IMAP_FOLDER
                        IMAP folder(s) (comma-separated) to retrieve mails from, default INBOX
  -L, --list-messages-only
                        list messages in IMAP folder only
  -m MSGS, --msgs MSGS  retrieve messages in MSGS range only, e.g. "1-3,5", default all
  -o OUTPUT, --output OUTPUT
                        write JSON/CSV to OUTPUT file
  -C, --csv             use CSV output format (instead of JSON)
  -O, --overview        create overview of objects and observations
  -D, --sort-by-date    sort overview by observation date (minus 12h)

Version 1.5 / 2024-06-26 / Martin Junius
```

Config data for IMAP mailbox is stored in imap-account.json

Examples:
```
mpc-retrieve-ack.py -l
```
List mailbox folders

```
mpc-retrieve-ack.py -f INBOX.Archive -L
```
List messages in folder INBOX.Archive

```
mpc-retrieve-ack.py -f INBOX.Archive -o ack-mails.json
```
Retrieve all ACK mails from INBOX.Archvie, query WAMO, and write results to ack-mails.json

```
mpc-retrieve-ack.py -f ARCHIVE -O -o report.txt
```
Retrieve all ACK mails from ARCHIVE folder, query WAMO, and write overview list to report.txt (sorted by object)

```
mpc-retrieve-ack.py -f ARCHIVE -O -o report.txt -D
```
Retrieve all ACK mails from ARCHIVE folder, query WAMO, and write overview list to report.txt (sorted by date/time)

```
mpc-retrieve-ack-py -f ARCHIVE -C -o report.csv
```
Retrieve all ACK mails from ARCHIVE folder, query WAMO, and write detailed data to CSV output report.csv


## mpc-retrieve-reports
Retrieve Minor Planets Center observation data from locally stored MPC1992/ADES report txt files, and MPC WAMO service

```
usage: mpc-retrieve-reports [-h] [-v] [-d] [-n] [-M] [-A] [-o OUTPUT] [-C] [-O] [-D] directory [directory ...]

Retrieve MPC reports

positional arguments:
  directory             read MPC reports from directory/file instead of ACK mails

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose messages
  -d, --debug           more debug messages
  -n, --no-wamo-requests
                        don't request observations from minorplanetcenter.net WAMO
  -M, --mpc1992-reports
                        read old MPC 1992 reports
  -A, --ades-reports    read new ADES (PSV format) reports
  -o OUTPUT, --output OUTPUT
                        write JSON/CSV to OUTPUT file
  -C, --csv             use CSV output format (instead of JSON)
  -O, --overview        create overview of objects and observations
  -D, --sort-by-date    sort overview by observation date (minus 12h)

Version 1.5 / 2024-06-26 / Martin Junius
```

Examples:

```
mpc-retrieve-reports.py -A -o ades-reports.json '\Users\someone\Asteroids\reports\'
```
Retrieve all ADES report file from the given directory (recursively), query WAMO, and write results to ades-reports.json

