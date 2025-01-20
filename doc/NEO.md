# NEO Observations with N.I.N.A and the IAS Astro Python Scripts

## N.I.N.A Profiles

### IAS Telescope Remote2

### IAS Telescope Remote3
Use profiles "Remote3 NEO PHD2" (guiding) or "Remote3 NEO" (tracking only).

Images are store under Image file path > _asteroids_YYYY-MM-DD > TARGET, must be the same as the "subdir" setting in nina-create-sequence.json. All dates use the DATEMINUS12 convention.

N.I.N.A Image file pattern setting: ```_asteroids_$$DATEMINUS12$$\$$TARGETNAME$$\$$TARGETNAME$$_```[...]


## nina-create-sequence2

Target names are created by nina-create-sequence2.py using the "format" setting in nina-create-sequence.json, currently "YYYY-MM-DD NNN OBJECT (nNNN)" (date, sequence #, object name, # of frames).

Create the complete N.I.N.A sequence for the observation night with:

```
nina-create-sequence2.py -v -S remote-neo M49_cam#3_Revise_2024-11-02-04-08-32.csv
```

Example output: 
```
nina-create-sequence2: processing target template ./NINA-Templates-IAS/Target NEO.template.json
nina-create-sequence2: processing sequence template ./NINA-Templates-IAS/Base NEO nautical.json
nina-create-sequence2: target format (0=target, 1=date, 2=seq, 3=number) {1} {2:03d} {0} (n{3:03d})
nina-create-sequence2: output format (1=date) NEO-{1}.json
nina-create-sequence2: add target items to container '', empty=target area
nina-create-sequence2: timezone Africa/Windhoek
nina-create-sequence2: subdir (1=date) _asteroids_{1}
nina-create-sequence2: destination directory D:\Users\remote\Documents\N.I.N.A
nina-create-sequence2: output file NEO-2024-11-02.json
nina-create-sequence2: NINATarget(process_data): name = Target NEO
nina-create-sequence2: NINASequence(process_data): name = Base NEO nautical
nina-create-sequence2: processing CSV file M49_cam#3_Revise_2024-11-02-04-08-32.csv
#001 target=2025-01-09 001 2021 VB7 (n110) RA=06 15 56.6 DEC=+18 31 20
     UT=2024-11-02 18:03:00+00:00 / local 2024-11-02 20:03:00+02:00
     110x2.0s filter=L
nina-create-sequence2: NINASequence(append_target): name = 2025-01-09 001 2021 VB7 (n110)
#002 target=2025-01-09 002 2024 TD22 (n042) RA=22 05 57.9 DEC=-03 20 43
     UT=2024-11-02 18:18:00+00:00 / local 2024-11-02 20:18:00+02:00
     42x6.0s filter=L
[...]
#020 target=2025-01-09 020 2024 TX13 (n015) RA=06 44 41.9 DEC=+27 32 53
     UT=2024-11-03 02:43:00+00:00 / local 2024-11-03 04:43:00+02:00
     15x2.0s filter=L
nina-create-sequence2: NINASequence(append_target): name = 2025-01-09 020 2024 TX13 (n015)
#021 target=2025-01-09 021 2024 TN1 (n018) RA=09 38 46.8 DEC=-23 10 27
     UT=2024-11-03 02:50:00+00:00 / local 2024-11-03 04:50:00+02:00
     18x30.6s filter=L
nina-create-sequence2: NINASequence(append_target): name = 2025-01-09 021 2024 TN1 (n018)
nina-create-sequence2: writing JSON sequence D:\Users\remote\Documents\N.I.N.A\NEO-2024-11-02.json
```

The new sequence NEO-2024-11-02.json is then ready to be loaded in N.I.N.A's advanced sequencer.


## nina-zip-data

nina-zip-data.py runs in parallel with the observation sequence in N.I.N.A, waiting for data to be flagged as ".ready":

```
nina-zip-data.py -v --ready --subdir=_asteroids
```

Example Output:

```
nina-zip-data: config file .\.config\nina-zip-config.json
nina-zip-data: config keys: numenor-onedrive numenor IAS-Hakos-3-old IAS-Hakos-3 Hakos-Lukas-NEW IAS-Hakos-2
nina-zip-data: Data directory = D:\Users\remote\Documents\NINA-Data
nina-zip-data: Dest directory = iasdata:remote-upload3
nina-zip-data: Dest subdir    = 2025/01
nina-zip-data: Tmp directory  = D:\Users\remote\Documents\NINA-Tmp
nina-zip-data: 7z program     = C:\Program Files\7-Zip\7z.exe
nina-zip-data: rclone program = C:\Tools\rclone\rclone.exe
nina-zip-data: Use rclone     = True
nina-zip-data: Date minus 12h = 2025-01-09
nina-zip-data: Sub directory  = _asteroids_2025-01-09
nina-zip-data: WARNING: directory D:\Users\remote\Documents\NINA-Data\_asteroids_2025-01-09 doesn't exist, creating it
nina-zip-data: scanning directory D:\Users\remote\Documents\NINA-Data\_asteroids_2025-01-09
Waiting for ready data ... (Ctrl-C to interrupt)
```

Once a target is finished, all data will be packed in a 7z archive and uploaded (output from older test data):

```
nina-zip-data: target ready: 2023-07-07 006 P21GNQJ (n039)
2025-01-16 11:03:39 archiving target 2023-07-07 006 P21GNQJ (n039)
==================================================================
nina-zip-data: zip file D:\Users\remote\Documents\NINA-Tmp\2023-07-07 006 P21GNQJ (n039).7z
nina-zip-data: run C:\Program Files\7-Zip\7z.exe a -t7z -mx5 -r -spf D:\Users\remote\Documents\NINA-Tmp\2023-07-07 006 P21GNQJ (n039).7z 2023-07-07 006 P21GNQJ (n039)

7-Zip 24.09 (x64) : Copyright (c) 1999-2024 Igor Pavlov : 2024-11-29

Scanning the drive:
1 folder, 2 files, 26121600 bytes (25 MiB)

Creating archive: D:\Users\remote\Documents\NINA-Tmp\2023-07-07 006 P21GNQJ (n039).7z

Add new data to archive: 1 folder, 2 files, 26121600 bytes (25 MiB)

Files read from disk: 2
Archive size: 11109864 bytes (11 MiB)
Everything is Ok
==================================================================
nina-zip-data: upload to iasdata:test-upload (+subdir)
nina-zip-data: run C:\Tools\rclone\rclone.exe moveto D:\Users\remote\Documents\NINA-Tmp\2023-07-07 006 P21GNQJ (n039).7z iasdata:test-upload/_asteroids/2023/07/_asteroids_2023-07-07/2023-07-07 006 P21GNQJ (n039).7z -v -P
2025/01/16 11:03:55 INFO  : 2023-07-07 006 P21GNQJ (n039).7z: Copied (new)
2025/01/16 11:03:55 INFO  : 2023-07-07 006 P21GNQJ (n039).7z: Deleted
Transferred:       10.595 MiB / 10.595 MiB, 100%, 2.644 MiB/s, ETA 0s
Checks:                 1 / 1, 100%
Deleted:                1 (files), 0 (dirs), 10.595 MiB (freed)
Renamed:                1
Transferred:            1 / 1, 100%
Elapsed time:         4.8s
2025/01/16 11:03:55 INFO  :
Transferred:       10.595 MiB / 10.595 MiB, 100%, 2.644 MiB/s, ETA 0s
Checks:                 1 / 1, 100%
Deleted:                1 (files), 0 (dirs), 10.595 MiB (freed)
Renamed:                1
Transferred:            1 / 1, 100%
Elapsed time:         4.8s
==================================================================
```

Archives will be uploaded to the buckets remote-upload2 / remote-upload3 (here it's test-upload) and a subdirectory structure SUBDIR/YYYY/MM/SUBDIR_YYYY-MM-DD. SUBDIR (--subdir option) for NEOs is "_asteroids".
