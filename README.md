# IAS Astro Python Tools

Python scripts for automation of NEO observations with N.I.N.A (and more)
- Build JSON sequences from target templates and observation data in CSV format
- Test Hakos roof and parked status
- Data packing with 7-zip and upload
- Analysis of autofocus results with CSV output
- Count # of frames in data directory, output CSV for Astrobin import
- Process MPC ACK mails and retrieve observations from MPC WAMO
- Process MPC 1992 and ADES reports, retrieve observations from MPC WAMO

Copyright 2023-2025 Martin Junius

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

The following additional Python libraries must be installed, see also requirements.txt:

| Library  | PyPI URL                           |
| -------- | ---------------------------------- |
| requests | https://pypi.org/project/requests/ |
| psutil   | https://pypi.org/project/psutil/   |
| icecream | https://pypi.org/project/icecream/ |
| tzdata   | https://pypi.org/project/tzdata/   (support for IANA timezone names on Windows) |

The following external programs are required and must be installed:

| Program | URL |
| ------- | --- |
| 7-zip   | https://7-zip.com/ |
| rclone  | https://rclone.org/downloads/ |

Local modules:

| Library          | Function                           |
| ---------------- | ---------------------------------- |
| mpc.mpcdata80    | Class for handling MPC 80-column data format |
| mpc.mpcosarchive | Class for handling MPC/MPO/MPS archive |
| mpc.mpcwamo      | Functions for handling WAMO requests |
| jsonconfig       | Read/write JSON config files for the astro scripts |
| verbose          | verbose(), warning() and error() messages |
| csvoutput        | Handle output to CSV file |
| discordmsg       | Send message via Discord webhook |
| jsonoutput       | Handle output to JSON file |
| ovoutput         | Handle output to overview text file |
| radec            | Class Coord for handling RA/DEC coordinates |



## nina-create-sequence2
Improved version of nina-create-sequence, builds a complete N.I.N.A sequence for the observation night, using a base template and a target template (repeated for every single object in the target area), from a CSV list of targets.

The directories NINA-Templates-IAS/, NINA-Templates-IAS3/ and NINA-Templates-Common/ contain the necessary N.I.N.A templates.

Currently used for the M49, the IAS Remote Telescopes at Hakos, Namibia

```
usage: nina-create-sequence2 [-h] [-v] [-d] [-A] [-D DESTINATION_DIR] [-o OUTPUT] [-n] [-S SETTING] [--date DATE] filename [filename ...]

Create/populate multiple N.I.N.A target templates/complete sequence with data from NEO Planner CSV

positional arguments:
  filename              CSV target data list

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -d, --debug           more debug messages
  -A, --debug-print-attr
                        extra debug output
  -D DESTINATION_DIR, --destination-dir DESTINATION_DIR
                        output dir for created sequence
  -o OUTPUT, --output OUTPUT
                        output .json file
  -n, --no-output       dry run, don't create output files
  -S SETTING, --setting SETTING
                        use template/target SETTING from config
  --date DATE           use DATE for generating sequence (default 2024-09-04)

Version: 1.4 / 2024-09-02 / Martin Junius
```

Config: nina-create-sequence.json


## test-hakos-roof
For Hakos remote observatories roll-off roof control only, refactored status queries

```
usage: test-hakos-roof [-h] [-v] [-d] [-P] [-U] [-O]

Test Hakos roof (shutter) status: returns exit code 0, if ok (open/parked/unparked), else 1

options:
  -h, --help      show this help message and exit
  -v, --verbose   debug messages
  -d, --debug     more debug messages
  -P, --parked    test for "parked" status
  -U, --unparked  test for "unparked" status
  -O, --open      test for "open" status (default)

Version 1.1 / 2024-07-17 / Martin Junius
```

Config file: hakosroof.json


## N.I.N.A External Script
Use the batch files/wrappers with full path in N.I.N.A's "External Script" instruction, e.g.

```
"D:\Users\remote\Documents\Scripts\test-hakos-roof.bat"
"D:\Users\remote\Documents\Scripts\nina-flag-ready.bat" "TARGET"
"D:\Users\remote\Documents\Scripts\discord-aag.bat"
```


## astro-countsubs
Count sub frames in directory structure and compute total exposure time. Relies on *YYYY-MM-DD sub-directories and FITS filenames containing filter name and exposure time. Additional data on calibration from JSON config file.

```
usage: astro-countsubs [-h] [-v] [-d] [-x EXCLUDE] [-f FILTER] [-t EXPOSURE_TIME] [-C] [-o OUTPUT] [-F FILTER_SET] [--calibration-set CALIBRATION_SET]
                       [-m MATCH] [--target] [-T] [-N] [-M]
                       dirname

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
                        filter list, e.g. L,R,G,B
  -t EXPOSURE_TIME, --exposure-time EXPOSURE_TIME
                        exposure time (sec) if not present in filename
  -C, --csv             output CSV list for Astrobin
  -o OUTPUT, --output OUTPUT
                        write CSV to file OUTPUT (default: stdout)
  -F FILTER_SET, --filter-set FILTER_SET
                        name of filter set for Astrobin CSV (see config)
  --calibration-set CALIBRATION_SET
                        name of calibration set (see config)
  -m MATCH, --match MATCH
                        filename must contain MATCH
  --target              include target name in date stats
  -T, --total-only      list total only
  -N, --no-calibration  don't list calibration data
  -M, --markdown        output markdown table

Version: 1.4 / 2024-12-07 / Martin Junius
```

Config file astro-countsubs-config.json

Examples:

```
astro-countsubs.py --filter-set "Astronomik 2in" --calibration-set ak3-asi294mc-2024 --filter L '\Images\NGC 6744\'
```
OSC with just an Astronomik L-2 filter, text output

```
astro-countsubs.py --filter-set "Baader 36mm" --calibration-set remote3 --csv -o tmp/NGC5139.csv '\Images\NGC 5139\'
```
Mono camera with Baader filter set, output CSV file for Astrobin import


## nina-zip-data
Automatically archive N.I.N.A exposure when a target sequence has been completed,
relying on the .ready flags created by nina-flag-ready.bat, or for all/selected
targets of an observation night.

Supersedes nina-zip-ready-data and nina-zip-last-night.

```
usage: nina-zip-data [-h] [-v] [-d] [-n] [-l] [--ready] [--last] [--date DATE] [--subdir SUBDIR] [--targets TARGETS] [--hostname HOSTNAME]
                     [-t TIME_INTERVAL] [-m MX]

Zip (7z) N.I.N.A data and upload

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug messages
  -d, --debug           more debug messages
  -n, --no-action       dry run
  -l, --low-priority    set process priority to low
  --ready               run in TARGET.ready mode
  --last                run in last night mode (2024-10-05)
  --date DATE           run in archive data from DATE mode
  --subdir SUBDIR       search SUBDIR_YYYY-MM-DD in data dir for ready targets (--ready)
  --targets TARGETS     archive TARGET[,TARGET] only (--last / --date)
  --hostname HOSTNAME   load settings for HOSTNAME (default numenor)
  -t TIME_INTERVAL, --time-interval TIME_INTERVAL
                        time interval for checking data directory (default 60s)
  -m MX, --mx MX        7-Zip compression setting -mx (default 5), 0=none, 1=fastest, 3=fast, 5=normal, 7=max, 9=ultra

Version 1.5 / 2024-10-05 / Martin Junius
```

### --ready / --subdir mode
Automatically archive N.I.N.A exposure when a target sequence has been completed,
relying on the .ready flags created by nina-flag-ready.bat run as an External Script
from within N.I.N.A
- Search TARGET.ready files in DATADIR, optional DATADIR/SUBDIR_YYYY-MM-DD
- Look for corresponding TARGET.7z archive in TMPDIR or ZIPDIR
- If exists, skip
- If not, run 7z.exe to archive TARGET data subdir in DATA to TARGET.7z in ZIPDIR
- Loop continuously

### --last / --date mode
Archive all N.I.N.A data from the last observation night (or date given by the --date option)
- Search all TARGET[/_-]YYYY-MM-DD directories in DATADIR (optional DATA/SUBDIR)
- Look for corresponding TARGET-YYYY-MM-DD.7z archive in TMPDIR or ZIPDIR
- If exists, skip
- If not, run 7z.exe to archive TARGET/YYYY-MM-DD data subdir in DATA to TARGET-YYYY-MM-DD.7z in ZIPDIR

Setting --date implies --last, --subdir implies --ready, add an extra --ready or --last to
override this behavior.

Config file: nina-zip-config.json



## nina-af-analyzer
Quick'n'dirty analysis of N.I.N.A autofocus results, with CSV output.

```
usage: nina-af-analyzer [-h] [-v] [-d] [-m MATCH] [-o OUTPUT] [-C] [dirname ...]

N.I.N.A Autofocus results analyzer

positional arguments:
  dirname               directory name (default: LOCALAPPDATA)

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose messages
  -d, --debug           more debug messages
  -m MATCH, --match MATCH
                        process files matching profile code MATCH
  -o OUTPUT, --output OUTPUT
                        write CSV to OUTPUT file
  -C, --csv             use CSV output format

Version 0.1 / 2024-08-12 / Martin Junius
```

## mpc-retrieve-ack
Retrieve Minor Planets Center observation data from IMAP server with ACK mails, and MPC WAMO service

```
usage: mpc-retrieve-ack [-h] [-v] [-d] [-n] [-l] [-f IMAP_FOLDER] [-L] [-m MSGS] [-M MATCH] [-o OUTPUT] [-J] [-C] [-O] [-S] [-D]

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
  -M MATCH, --match MATCH
                        retrieve messages with subject containing MATCH
  -o OUTPUT, --output OUTPUT
                        write to OUTPUT file
  -J, --json            use JSON output format
  -C, --csv             use CSV output format
  -O, --overview        create overview of objects and observations
  -S, --submitted       add submitted observation to overview
  -D, --sort-by-date    sort overview by observation date (minus 12h)

Version 1.8 / 2024-11-10 / Martin Junius
```

Config file: imap-account.json

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
  -C, --csv             use CSV output format (instead of JSON), NOT YET IMPLEMENTED
  -O, --overview        create overview of objects and observations
  -D, --sort-by-date    sort overview by observation date (minus 12h)

Version 1.6 / 2024-07-15 / Martin Junius
```

Examples:

```
mpc-retrieve-reports.py -A -o ades-reports.json '\Users\someone\Asteroids\reports\'
```
Retrieve all ADES report file from the given directory (recursively), query WAMO, and write results to ades-reports.json


## discord-aag
Send AAG Cloudwatcher Solo status to Discord channel

```
usage: discord-aag [-h] [-v] [-d] [-A AAG_JSON] [-C CHANNEL]

Send AAG status to Discord channel

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose messages
  -d, --debug           more debug messages
  -A AAG_JSON, --aag-json AAG_JSON
                        path to AAG Cloudwatcher Solo status file
  -C CHANNEL, --channel CHANNEL
                        channel name to match in JSON discord-config

Version 0.1 / 2024-12-27 / Martin Junius
```


## JSON Config Files

All the scripts search the corresponding JSON config in the following directories and in this order:
- Current directory/.config/
- Current directory/.config/astro-python/
- %LOCALAPPDATA%/astro-python/
- %APPDATA%/astro-python/
- All directories from Python search path sys.path with added /.config/

See sample-config/ in the repository for configuration examples.
