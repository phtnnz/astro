# N.I.N.A Automation

This document collects various information for automating N.I.N.A (target) templates and sequences (JSON).

## Example Timings for the IAS Remote Telescope

| # | Number | Exp.time | Scheduled | Slew start | Slew end | AF start | AF end   | Exp start | Flip start | Flip end | Exp end  |
|---|--------|----------|-----------|------------|----------|----------|----------|-----------|------------|----------|----------|
|1  | 15     | 36.4     | 20:13:00  | 20:14:15   | 20:15:16 | 20:15:16 | 20:16:56 | 20:16:56  |            |          | 20:26:31 |
|   |        |          |           |            |      61s |          |     100s |           |            |          |     565s |
|   |        |          |           |            |          |          |          |           |            |          |   37.7s = +1.3s / img |
|2  | 15     | 60       | 20:25:00  | 20:26:31   | 20:27:34 | 20:27:34 | 20:29:14 | 20:29:14  | 20:33:22   | 20:36:53 | 20:48:15 |
|   |        |          |           |            |      63s |          |     100s |           |            |     211s |     1141-211s |
|   |        |          |           |            |          |          |          |           |            |          |   62s = +2.0s / img |
|3  | 52     | 19.7     | 20:43:00  | 20:48:15   | 20:49:47 | 20:49:47 | 20:51:28 | 20:51:29  |            |          | 21:09:48 |
|   |        |          |           |            |      92s |          |     101s |           |            |          |     1099s |
|   |        |          |           |            |          |          |          |           |            |          |   21.1s = +1.4s / img |
|4  | 75     | 2.2      | 21:04:00  | 21:09:53   | 21:11:02 | 21:11:02 | 21:12:51 | 21:12:51  |            |          | 21:17:26 |
|   |        |          |           |            |      69s |          |     109s |           |            |          |     275s |
|   |        |          |           |            |          |          |          |           |            |          |   3.7s = +1.5s / img |
|5  | 75     | 2.2      | 21:12:00  | ...

## Values for Calculation

Slew/center time = 90s

AF time = 100s

Meridian flip time = 210s

Overhead time per image = 1.5s
