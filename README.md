# WBSO logging tool

Log your work by description and timestamps for later export to a logging system.

Copyright Sightcorp 2019.

## Installation

1. Clone the repository in your location of choice.
2. To use command `wbso` instead of `python <repo>/wbso.py` add the following line to `~/.bashrc`:

```bash
alias wbso="python3 <repo-path>/wbso.py"
```

## Usage

1. `wbso`: show the current logs.
2. `wbso <start> <end> <description>`: log a new session. Times are in format `HH:SS`. End times can be omitted to open an ongoing session. Start times can be omitted to start the new session at the current timestamp. Please refer to `wbso --help` for all usage patterns for logging.
3. `wbso <start> <end> -r <index>`: "resume" a session by copying it's description to the new session. Start and end times can be omitted analogous to pattern 2. Index refers to the index of the log when shown using `wbso`.
4. `wbso -c <end>`: close an ongoing/open session. End time can be omitted to use the current timestamp.
5. `wbso -d <index`: delete a session.
6. `wbso --clear`: delete all sessions.
7. `wbso --export`: export all sessions as comma-separated lines. This format is compatible with the Sightcorp WBSO logging spreadsheet.

## Exporting to Sightcorp WBSO

1. Use `wbso --export` to print all sessions in comma-separated format.
2. Copy-paste the sessions into the spreadsheet. Use the "Split to columns" feature to automatically match the desired format.
3. Manually assign the projects for each session.
