#!/usr/bin/env python
"""
Log your WBSO work by timestamps. Calling without arguments shows the recorded
sessions.

Usage:
    wbso.py
    wbso.py DESCRIPTION
    wbso.py START DESCRIPTION
    wbso.py START END DESCRIPTION
    wbso.py (--close|-c) [(--time|-t) ENDTIME]
    wbso.py (--resume|-r) [INDEX]
    wbso.py (--delete|-d) INDEX
    wbso.py --clear
    wbso.py --export [--merge|-m]

Options:
    --log -l                Log a session, optionally providing start and end times
    --open -o               Alias for --log
    --close -c              End the current work session
    --resume -r             Resume the last session by duplicating it's description to a new open session
    --delete -d             Delete a session by index number
    --clear                 Clear all WBSO sessions
    --export                Export all sessions to comma-separated format for spreadsheets

Copyright Sightcorp 2018.
"""
import docopt
import time
import datetime
import csv
import os
import pickle


def _time_to_datetime(time_str):
    time_format = "%H:%M"
    struct_time = time.strptime(time_str, time_format)
    now = datetime.datetime.today()
    return datetime.datetime(now.year, now.month, now.day,
                                struct_time.tm_hour,
                                struct_time.tm_min,
                                struct_time.tm_sec)

def _duration_as_hours(start, end):
    duration = end - start
    return duration.total_seconds() / 3600

class Sessions(object):
    def __init__(self):
        self.sessions = []
        self.open_session = None

    def start(self, description, start=None):
        if self.open_session is not None:
            raise ValueError(f"There is already an open session:\n{self.get_open()}")

        if start:
            start = _time_to_datetime(start)
        else:
            start = datetime.datetime.now()

        new_session = Session(start, end=None, description=description)
        self.sessions.append(new_session)
        self.open_session = len(self.sessions)-1

    def end(self, end_time=None):
        if self.open_session is None:
            return False
        open_session = self.sessions[self.open_session]

        if end_time:
            open_session.end = _time_to_datetime(end_time)
        else:
            open_session.end = datetime.datetime.now()
        self.open_session = None

    def log(self, start, end, description):
        self.sessions.append(Session(
            _time_to_datetime(start),
            _time_to_datetime(end),
            description
        ))

    def remove(self, index):
        del self.sessions[index]
        if self.open_session is not None:
            if self.open_session == index:
                self.open_session = None
            elif self.open_session > index:
                self.open_session -= 1

    def clear(self):
        self.sessions = []
        self.open_session = None

    def get_all(self):
        return self.sessions

    def get_open(self):
        return self.sessions[self.open_session]

    def __str__(self):
        lines = []
        for i, session in enumerate(self.sessions):
            lines.append(f"{i}. {session}")
        return "\n".join(lines)

class Session(object):

    def __init__(self, start, end=None, description=""):
        self.start = start
        self.end = end
        self.description = description

    def __str__(self):
        start_time_format = "%a, %d %b %H:%M:%S"
        end_time_format = "%H:%M:%S"
        next_day_end_time_format = "%d %b %H:%M:%S"
        start_str = self.start.strftime(start_time_format)
        if self.end is None:
            end_str = '...'
        else:
            end_str = self.end.strftime(end_time_format)
            # If start and end are not on the same day, add the date to the end
            if self.start.day != self.end.day:
                end_str = self.end.strftime(next_day_end_time_format)
        return "{:s} - {:s}: {:s}".format(start_str, end_str, self.description)

    def tab_spaced_str(self):
        """
        Format: `{date}   {empty for category}  {description}   {duration}`
        """
        date_format = "%Y-%m-%d"
        formatted_start = self.start.strftime(date_format)
        duration = _duration_as_hours(self.start, self.end)
        formatted_duration = f"{duration:.8f}"

        return f"{formatted_start},,{self.description},{formatted_duration}"

LOG_FILE = '/home/robert-jan/wbso/wbso_log.pickle'
SESSIONS = Sessions()


def load():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            pass
        print("Created new log file.")
        return Sessions()

    with open(LOG_FILE, 'rb') as f:
        sessions = pickle.load(f)
        return sessions

def save(sessions):
    with open(LOG_FILE, 'wb') as f:
        pickle.dump(sessions, f)

if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='WBSO logging v1.0.0')

    SESSIONS = load()

    if args['--close']:
        # Close
        if not SESSIONS.end(end_time=args['ENDTIME']):
            print("No session to close.")
        print(SESSIONS)

    elif args['--resume']:
        # Resume: duplicate last session as open session
        if len(SESSIONS.get_all()) == 0:
            print("No session to resume.")
        else:
            session_index = -1
            if args['INDEX']:
                session_index = int(args['INDEX'])
            session_to_resume = SESSIONS.get_all()[session_index]
            SESSIONS.start(session_to_resume.description)
            print(SESSIONS)

    elif args['--delete']:
        # Delete
        SESSIONS.remove(int(args['INDEX']))
        print("Sessions:")
        print(SESSIONS)

    elif args['--clear']:
        # Clear
        nr_sessions = len(SESSIONS.get_all())
        SESSIONS.clear()
        print(f"{nr_sessions} sessions cleared.")

    elif args['DESCRIPTION']:
        # Log / open
        if args['END']:
            SESSIONS.log(args['START'], args['END'], args['DESCRIPTION'])
            print(SESSIONS)
        else:
            SESSIONS.start(args['DESCRIPTION'], args['START'])
            print(SESSIONS)

    elif args['--export']:
        # Export
        if SESSIONS.open_session is not None:
            print("Cannot export while a session is open.")
            print(SESSIONS)

        sessions = SESSIONS.get_all()
        if len(sessions) == 0:
            print("No sessions.")

        sess_durations = {}
        for session in sessions:
            # Get date and duration
            date_format = "%Y-%m-%d"
            date = session.start.strftime(date_format)
            duration = _duration_as_hours(session.start, session.end)

            # Store sessions by date, then description
            if date not in sess_durations:
                sess_durations[date] = {}
            if session.description not in sess_durations[date]:
                sess_durations[date][session.description] = 0
            sess_durations[date][session.description] += duration

        # Export each unique tuple (date, description)
        for date in sess_durations:
            for description in sess_durations[date]:
                print(f"{date},,{description},{sess_durations[date][description]:.8f}")

    else:
        # Report
        if SESSIONS.open_session:
            print(f"Open session: \n{SESSIONS.get_open()}")
        if len(SESSIONS.get_all()) == 0:
            print("No sessions.")
        else:
            print("Sessions:")
            print(str(SESSIONS))

    save(SESSIONS)