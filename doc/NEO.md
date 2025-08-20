# NEO Observations with N.I.N.A and the IAS Astro Python Scripts

## N.I.N.A Profiles

### IAS Telescope Remote2
Use profile "IAS Remote 10" PHD2 NEOs".

### IAS Telescope Remote3
Use profiles "Remote3 NEO PHD2" (guiding) or "Remote3 NEO" (tracking only).

Images are store under Image file path > _asteroids_YYYY-MM-DD > TARGET, must be the same as the "subdir" setting in nina-create-sequence.json. All dates use the DATEMINUS12 convention.

N.I.N.A Image file pattern setting: ```_asteroids_$$DATEMINUS12$$\$$TARGETNAME$$\$$TARGETNAME$$_```[...]


## nina-create-sequence2

Target names are created by nina-create-sequence2.py using the "format" setting in nina-create-sequence.json, currently "YYYY-MM-DD NNN OBJECT (nNNN)" (date, sequence #, object name, # of frames).

Create the complete N.I.N.A sequence for the observation night with:

```
nina-create-sequence2.py -v --setting common-neo M49_cam#3_Revise_2025-08-20-03-39-33.csv
```

Example output: 

```
nina-create-sequence2: processing target template ./NINA-Templates-IAS-Common/Target NEO (Discord).template.json
nina-create-sequence2: processing sequence template ./NINA-Templates-IAS-Common/Base NEO NAUTICAL (Discord).json
nina-create-sequence2: target format (0=target, 1=date, 2=seq, 3=number) {1} {2:03d} {0} (n{3:03d})
nina-create-sequence2: output format (1=date) NEO-{1}.json
nina-create-sequence2: add target items to container '', empty=target area
nina-create-sequence2: timezone Africa/Windhoek
nina-create-sequence2: subdir (1=date) _asteroids_{1}
nina-create-sequence2: destination directory D:\Users\mj\Documents\N.I.N.A
nina-create-sequence2: output file NEO-2025-08-20.json
nina-create-sequence2: NINATarget(process_data): name = Target NEO (Discord)
nina-create-sequence2: NINASequence(process_data): name = Base NEO NAUTICAL (Discord)
nina-create-sequence2: processing CSV file D:\Users\mj\OneDrive\Astro-Data\NEO-Planner\M49_cam#3_Revise_2025-08-20-03-39-33.csv
#001 target=2025-08-20 001 C2023 T3 (n015) RA=14 06 53.3 DEC=-20 43 28
     UT=2025-08-20 17:35:00+00:00 / local 2025-08-20 19:35:00+02:00   
     15x60.0s filter=L
nina-create-sequence2: NINASequence(append_target): name = 2025-08-20 001 C2023 T3 (n015)
#002 target=2025-08-20 002 C2021 G2 (n015) RA=15 14 12.0 DEC=-00 36 48
     UT=2025-08-20 17:57:00+00:00 / local 2025-08-20 19:57:00+02:00
     15x60.0s filter=L
[...]
#017 target=2025-08-20 017 5GO4M21 (n036) RA=03 01 18.0 DEC=-24 54 48
     UT=2025-08-21 00:56:00+00:00 / local 2025-08-21 02:56:00+02:00
     36x60.0s filter=L
nina-create-sequence2: NINASequence(append_target): name = 2025-08-20 017 5GO4M21 (n036)
nina-create-sequence2: writing JSON sequence D:\Users\mj\Documents\N.I.N.A\NEO-2025-08-20.json
```

The new sequence NEO-2025-08-20.json is then ready to be loaded in N.I.N.A's advanced sequencer.
As of 2025-08-20, the sequence works with N.I.N.A. 3.1.2 and 3.2 BETA2.


## nina-zip-data

nina-zip-data.py runs in parallel with the observation sequence in N.I.N.A, waiting for data to be flagged as ".ready". Compression is set to fastest to speed up the archiving.

```
nina-zip-data.py -v --ready --subdir=_asteroids --mx 1
```

Example Output:

```
nina-zip-data.py -v --ready --subdir=_asteroids
nina-zip-data: config file .\.config\nina-zip-config.json
nina-zip-data: config keys: numenor-onedrive numenor IAS-Hakos-3-old IAS-Hakos-3 Hakos-Lukas-NEW IAS-Hakos-2
nina-zip-data: Data directory = D:\Users\remote\Documents\NINA-Data
nina-zip-data: Dest directory = iasdata:remote-upload2
nina-zip-data: Dest subdir    = 2025/08
nina-zip-data: Tmp directory  = D:\Users\remote\Documents\NINA-Tmp
nina-zip-data: 7z program     = C:\Program Files\7-Zip\7z.exe
nina-zip-data: rclone program = C:\Tools\rclone\rclone.exe
nina-zip-data: Use rclone     = True
nina-zip-data: Date minus 12h = 2025-08-20
nina-zip-data: Subdir         = _asteroids
nina-zip-data: WARNING: directory D:\Users\remote\Documents\NINA-Data\_asteroids_2025-08-20 doesn't exist, creating it
nina-zip-data: scanning directory D:\Users\remote\Documents\NINA-Data\_asteroids_2025-08-20
Waiting for ready data ... (Ctrl-C to interrupt)
```

Once a target is finished, all data will be packed in a 7z archive and uploaded (output from older test data):

```
[...]
nina-zip-data: target ready: 2025-08-20 003 P22d84P (n036)
2025-08-20 21:13:05 archiving target 2025-08-20 003 P22d84P (n036)
==================================================================
nina-zip-data: zip file D:\Users\remote\Documents\NINA-Tmp\2025-08-20 003 P22d84P (n036).7z
nina-zip-data: run C:\Program Files\7-Zip\7z.exe a -t7z -mx1 -r -spf D:\Users\remote\Documents\NINA-Tmp\2025-08-20 003 P22d84P (n036).7z 2025-08-20 003 P22d84P (n036)

7-Zip 25.00 (x64) : Copyright (c) 1999-2025 Igor Pavlov : 2025-07-05

Scanning the drive:
1 folder, 42 files, 470266473 bytes (449 MiB)

Creating archive: D:\Users\remote\Documents\NINA-Tmp\2025-08-20 003 P22d84P (n036).7z

Add new data to archive: 1 folder, 42 files, 470266473 bytes (449 MiB)

Files read from disk: 42
Archive size: 232694852 bytes (222 MiB)
Everything is Ok
==================================================================
nina-zip-data: upload to iasdata:remote-upload2 (+subdir)
nina-zip-data: run C:\Tools\rclone\rclone.exe moveto D:\Users\remote\Documents\NINA-Tmp\2025-08-20 003 P22d84P (n036).7z iasdata:remote-upload2/_asteroids/2025/08/_asteroids_2025-08-20/2025-08-20 003 P22d84P (n036).7z -v -P
2025/08/20 21:22:35 INFO  : 2025-08-20 003 P22d84P (n036).7z: Copied (new)
2025/08/20 21:22:35 INFO  : 2025-08-20 003 P22d84P (n036).7z: Deleted
Transferred:      221.915 MiB / 221.915 MiB, 100%, 165.286 KiB/s, ETA 0s
Checks:                 1 / 1, 100%
Deleted:                1 (files), 0 (dirs), 221.915 MiB (freed)
Renamed:                1
Transferred:            1 / 1, 100%
Elapsed time:      6m31.3s
2025/08/20 21:22:35 INFO  :
Transferred:      221.915 MiB / 221.915 MiB, 100%, 165.286 KiB/s, ETA 0s
Checks:                 1 / 1, 100%
Deleted:                1 (files), 0 (dirs), 221.915 MiB (freed)
Renamed:                1
Transferred:            1 / 1, 100%
Elapsed time:      6m31.3s
==================================================================
[...]
```

Archives will be uploaded to the buckets remote-upload2 / remote-upload3 and a subdirectory structure SUBDIR/YYYY/MM/SUBDIR_YYYY-MM-DD. SUBDIR (--subdir option) for NEOs is "_asteroids".
