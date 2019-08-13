#!/usr/bin/env python
"""
Log your WBSO work by timestamps. Calling without arguments shows the recorded
sessions. Where times are to be given, use format HH:MM or named times "now"
for the current timestamp or "last" for the end of the latest session.

Usage:
    wbso.py
    wbso.py (DESCRIPTION | (--resume|-r) [INDEX])
    wbso.py START (DESCRIPTION | (--resume|-r) [INDEX])
    wbso.py START END (DESCRIPTION | (--resume|-r) [INDEX])
    wbso.py (--close|-c) [ENDTIME]
    wbso.py (--delete|-d) INDEX
    wbso.py --cancel
    wbso.py --clear
    wbso.py --export
    wbso.py --amend [INDEX] DESCRIPTION

Options:
    --close -c              End the current work session
    --resume -r             Resume a session by duplicating it's description to this session
    --cancel                Delete the current work session
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
import json


def _duration_as_hours(start, end):
    duration = end - start
    return duration.total_seconds() / 3600

class Sessions(object):
    def __init__(self):
        self.sessions = []
        self.open_session = None

    def start(self, description, start=None):
        if self.open_session is not None:
            raise ValueError("There is already an open session:\n{:s}".format(self.get_open()))

        if start:
            start = self.time_to_datetime(start)
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
            open_session.end = self.time_to_datetime(end_time)
        else:
            open_session.end = datetime.datetime.now()

        self.open_session = None
        return True

    def log(self, start, end, description):
        self.sessions.append(Session(
            self.time_to_datetime(start),
            self.time_to_datetime(end),
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

    def get_last_end_time(self):
        if len(self.sessions) == 0:
            return None
        latest_end = self.sessions[0].end
        for session in self.sessions[1:]:
            if session.end > latest_end:
                latest_end = session.end
        return latest_end

    def time_to_datetime(self, time_str):
        if time_str == 'last':
            return self.get_last_end_time()
        elif time_str == 'now':
            return datetime.datetime.today()

        time_format = "%H:%M"
        struct_time = time.strptime(time_str, time_format)
        now = datetime.datetime.today()
        return datetime.datetime(now.year, now.month, now.day,
                                 struct_time.tm_hour,
                                 struct_time.tm_min,
                                 struct_time.tm_sec)

    def __str__(self):
        lines = []
        for i, session in enumerate(self.sessions):
            lines.append("{:d}. {:s}".format(i, str(session)))
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
        formatted_duration = "{:.2f}".format(duration)

        return "{:s},,{:s},{:s}".format(formatted_start, self.description, formatted_duration)

SESSIONS = Sessions()


def log_path():
    tool_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(tool_dir, 'wbso_log.pickle')

def load():
    log_file = log_path()

    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            pass
        print("Created new log file.")
        return Sessions()

    with open(log_file, 'rb') as f:
        sessions = pickle.load(f)
        return sessions

def save(sessions):
    log_file = log_path()

    with open(log_file, 'wb') as f:
        pickle.dump(sessions, f)

if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='WBSO logging v1.0.0')

    SESSIONS = load()

    if args['--close']:
        # Close
        if not SESSIONS.end(end_time=args['ENDTIME']):
            print("No session to close.")
        print(SESSIONS)

    elif args['--delete']:
        # Delete
        SESSIONS.remove(int(args['INDEX']))
        print("Sessions:")
        print(SESSIONS)

    elif args['--cancel']:
        # Cancel
        if SESSIONS.open_session != None:
            SESSIONS.remove(SESSIONS.open_session)
        else:
            print("No session to cancel.")
        print(SESSIONS)

    elif args['--clear']:
        # Clear
        nr_sessions = len(SESSIONS.get_all())
        SESSIONS.clear()
        print("{:d} sessions cleared.".format(nr_sessions))

    elif args['--amend']:
        # Amend
        session_index = -1
        if args['INDEX']:
            session_index = int(args['INDEX'])
        session_to_amend = SESSIONS.get_all()[session_index]
        session_to_amend.description = args['DESCRIPTION']
        print("Session amended:")
        print(session_to_amend)

    elif args['DESCRIPTION']:
        # Log / open
        if args['END']:
            SESSIONS.log(args['START'], args['END'], args['DESCRIPTION'])
            print(SESSIONS)
        else:
            SESSIONS.start(args['DESCRIPTION'], args['START'])
            print(SESSIONS)

    elif args['--resume']:
        # Resume: duplicate last session as open session
        if len(SESSIONS.get_all()) == 0:
            print("No session to resume.")
        else:
            session_index = -1
            if args['INDEX']:
                session_index = int(args['INDEX'])
            session_to_amend = SESSIONS.get_all()[session_index]

            # Log / open
            if args['END']:
                SESSIONS.log(args['START'], args['END'], session_to_amend.description)
                print(SESSIONS)
            else:
                SESSIONS.start(session_to_amend.description, args['START'])
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
                print("{:s},,{:s},{:.2f}".format(date, description, sess_durations[date][description]))

    else:
        # Report
        if SESSIONS.open_session:
            print("Open session: \n{:s}".format(str(SESSIONS.get_open())))
        if len(SESSIONS.get_all()) == 0:
            print("No sessions.")
        else:
            print("Sessions:")
            print(str(SESSIONS))

    save(SESSIONS)
