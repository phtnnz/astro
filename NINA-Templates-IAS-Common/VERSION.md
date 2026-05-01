# IAS Templates for Remote Telescopes @ Hakos

Version 2.0 / 2026-05-01 / Martin Junius

Required plugins: 
- 10 Micron Tools (remote2 only)
- ASA Tools (remote3 only)
- Sequencer Powerups
- Ground Station

All templates will send status messages to the corresponding Discord channel, which must be configured (webhook) in Ground Station setup.


## Base Sequences

### Base Remote2 (NAUTICAL)

Base sequence for telescope remote2 (10 Micron), contains all the necessary start-up and shutdown templates. Waits until astronomical dusk (default) or nautical dusk (variant NAUTICAL).

### Base Remote2 Epsilon

Base sequence for piggybacked Epsilon 130 on remote2.

### Base Remote3 (NAUTICAL)

Base sequence for telescope remote3 (ASA), otherwise same as for remote2.

### Base Loop Remote2 NAUTICAL

Base sequence variant for remote2, including Loop Objects NAUTICAL

### Base Loop Remote3 NAUTICAL

Base sequence variant for remote3, including Loop Objects NAUTICAL


## Start-up Templates

### Pre-Startup Remote2

Power-on 10u mount (Wake on LAN, configure broadcast IP in 10 Micron Tools setup!), switch on all devices, and connect all devices for main 10" Newtonian telescope

### Pre-Startup Remote2 Epsilon

Power-on 10u mount (Wake on LAN, configure broadcast IP in 10 Micron Tools setup!), switch on all devices, and connect all devices for piggybacked Epsilon 130 telescope

### Pre-Startup Remote3

Switch on all devices, connect all devices, and power-on motors (Autoslew)

### Startup when safe (NAUTICAL)

Check observatory roof/mount status, wait for safe conditions, open observatory roof, switch on fan, cool camera, wait for astronomical (default) / nautical dusk (variant NAUTICAL), switch off fan, unpark scope, stop tracking.


## Shutdown Templates

### Shutdown

Stop and park mount, close observatory roof, and warm camera.

### Post-Shutdown Remote2

Disconnect all devices, power off 10u mount, switch off all devices. (10 Micron Tools instruction Shutdown Mount followed by Disconnect may result in an error message, can be safely ignored.)

### Post-Shutdown Remote3

Power off motors (Autoslew), disconnect all devices, and switch off all devices.

### Post-Shutdwon Data Upload

Wait until sunrise + 1h, upload data to storage.



## Target Templates

### Target Generic

Generic target template: configurable start time, slew and center, auto-focus, checks object altitude, moon altitude, total exposure time 6h or until astronomical dawn, stop when condition becomes unsafe.

Exposure loop: 15x L 120s, 5x R/G/B 120s, 5x SII/Ha/OIII 180s

### Target OSC (rotate)

Dito for one-shot-color cameras, variant "rotate" with image rotation, exposure loop: 120s

### Target LRGB stars

Dito for e.g. star clusters, exposure loop: 15x L 60s, 5x R/G/B 60s

### Target RGB NB

Dito for narrowband + RGB stars, exposure loop: 5x R/G/B 60s, 5x SII/Ha/OIII 180s

### Target slew only

Slow and center, auto-focus only, wait for user interaction

### Target NEO

Special target template for NEO observations, used with ```nina-create-sequence2``` script.

### Target VS

Dito, special target template for variable stars observation, to be place inside Loop see below.


## Misc Templates

### Loop Objects (NAUTICAL)

Template for continous loop of e.g. Target VS objects.

### Waiting

Wait for user interaction (NINA message box).



## Assignment of Switch Ports (PegasusAstro UPBv2)

Switch 1-4 = 12 V Output 1-4, Switch 5-10 = USB3 1-4, USB2 5-6

### Remote2

| Switch | Port | Device |
| -------| ---- | ------ |
| 1  | Output 1 | TeenAstro Focuser       |
| 2  | Output 2 | QHY 268 M               |
| 3  | Output 3 | ASI 2600 MC + EAF       |
| 4  | Output 4 | Fan                     |
| 5  | USB3 1   | QHY 268 M               |
| 6  | USB3 2   | ASI 174 MM              |
| 7  | USB3 3   | ASI 2600 MC + CAA + EAF |
| 8  | USB3 4   | TeenAstro Focuser       |
| 9  | USB2 5   | -                       |
| 10 | USB2 6   | -                       |

### Remote3

| Switch | Port | Device |
| -------| ---- | ------ |
| 1  | Output 1 | QHY 268 M  |
| 2  | Output 2 | -          |
| 3  | Output 3 | MFOC       |
| 4  | Output 4 | Fan        |
| 5  | USB3 1   | QHY 268 M  |
| 6  | USB3 2   | -          |
| 7  | USB3 3   | -          |
| 8  | USB3 4   | -          |
| 9  | USB2 5   | MFOC       |
| 10 | USB2 6   | ASI 174 MM |
