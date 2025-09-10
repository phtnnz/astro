# IAS Templates for Remote Telescopes @ Hakos

Version 1.6 / 2025-09-10 / Martin Junius

Required plugins: 10 Micron Tools (remote2 only), ASA Tools (remote3 only), Connector, Discord Alert, Sequencer Powerups

All templates will send status messages to the corresponding Discord channels, which must be configured (webhook) in the Discord Alert setup.


## Base Sequences

### Base Remote2 (NAUTICAL)

Base sequence for telescope remote2 (10 Micron), contains all the necessary start-up and shutdown templates. Waits until astronomical dusk (default) or nautical dusk (variant NAUTICAL).

### Base Remote3 (NAUTICAL)

Base sequence for telescope remote3 (ASA), otherwise same as for remote2.


## Start-up Templates

### Pre-Startup Remote2

Power-on 10u mount (Wake on LAN, configure broadcast IP in 10 Micron Tools setup!), switch on all devices, and connect all devices.

### Pre-Startup Remote3

Switch on all devices, connect all devices, and power-on motors (Autoslew)

### Startup when safe (NAUTICAL)

Check observatory roof/mount status, wait for safe conditions, open observatory roof, switch on fan, wait for astronomical (default) / nautical dusk (variant NAUTICAL), switch off fan, and unpark scope (tracking stopped).


## Shutdown Templates

### Shutdown

Stop and park mount, close observatory roof, and warm camera.

### Post-Shutdown Remote2

Disconnect all devices, power off 10u mount, switch off all devices. (10 Micron Tools instruction Shutdown Mount followed by Disconnect may result in an error message, can be safely ignored.)

### Post-Shutdown Remote3

Power off motors (Autoslew), disconnect all devices, and switch off all devices.

### Post-Shutdwon Data Upload

Wait until sunrise + 1h, upload data to storage.

### Shutdown at twilight

Old shutdown templates, obsolete and will be removed in a future release.


## Target Templates

### Target Generic

Generic target template: configurable start time, slew and center, auto-focus, checks object altitude, moon altitude, total exposure time 6h or until astronomical dawn, stop when condition becomes unsafe.

Exposure loop: 15x L 120s, 5x R/G/B 120s, 5x SII/Ha/OIII 180s

### Target LRGB 

Dito for e.g. star clusters, exposure loop: 15x L 60s, 5x R/G/B 60s

### Target RGB NB

Dito for narrowband + RGB stars, exposure loop: 5x R/G/B 60s, 5x SII/Ha/OIII 180s

### Target slew only

Slow and center, auto-focus only, wait for user interaction

### Target NEO

Special target template for NEO observations, used with ```nina-create-sequence2``` script.

### Target VS

Dito, special target template for variable stars observation.


## Misc Templates

### Loop Objects (NAUTICAL)

Template for continous loop of e.g. Target VS objects.
