# -*- coding: utf-8 -*-

import time as _time
from datetime import datetime
from bisect import bisect_right

from .loader import Loader
from .timezone_info import TimezoneInfo
from .breakdown import Breakdown
from .transition_type import TransitionType

from .._compat import PY2


class Timezone(object):

    _cache = {}

    def __init__(self, name, transitions,
                 transition_types, default_transition_type):
        self._name = name
        self._transitions = transitions
        self._transition_types = transition_types
        self._default_transition_type = default_transition_type

    @property
    def name(self):
        return self._name

    @property
    def transitions(self):
        return self._transitions

    @classmethod
    def load(cls, name):
        """
        Loads a timezone with the given name or
        returns it from the cache.

        :param name: The name of the timezone
        :type name: str

        :rtype: Timezone
        """
        # Shortcut to UTC
        #if name.upper() == 'UTC':
        #    return UTC

        if name not in cls._cache:
            (transitions,
             transition_types,
             default_transition_type) = Loader.load(name)

            zone = cls(name,
                       transitions,
                       transition_types,
                       default_transition_type)

            cls._cache[name] = zone

        return cls._cache[name]

    def convert(self, dt):
        """
        Converts or normalizes a datetime.

        If there is no tzinfo set on the datetime, local time will be assumed
        and normalization will occur.

        Otherwise, it will convert the datetime to local time.
        """
        if dt.tzinfo is None:
            # we assume local time
            return self._normalize(dt)

        return self._convert(dt)

    def _normalize(self, dt):
        # if tzinfo is set, something wrong happened
        if dt.tzinfo is not None:
            raise ValueError(
                'A datetime with a tzinfo cannot be normalized. '
                'Use _convert() instead.'
            )

        if not self.transitions:
            # Use the default offset
            offset = self._default_transition_type.utc_offset
            unix_time = (dt - datetime(1970, 1, 1)).total_seconds() - offset

            return self._to_local_time(
                unix_time, self._default_transition_type
            )

        # Find the first transition after our target date/time
        begin = pre_tr = self._transitions[0]
        end = self._transitions[-1]
        offset = None

        if dt < begin.time:
            tr = begin
        elif not dt < end.time:
            tr = end
        else:
            # For some reason, Python 2.7 does not use
            # the Transition comparison methods.
            if PY2:
                transitions = map(lambda t: t.time, self._transitions)
            else:
                transitions = self._transitions

            idx = max(0, bisect_right(transitions, dt))
            tr = self._transitions[idx]

            if idx > 0:
                pre_tr = self._transitions[idx - 1]

                # DST -> No DST
                if dt <= pre_tr.pre_time:
                    tr = pre_tr

        transition_type = tr.transition_type
        if tr == begin:
            if not tr.pre_time < dt:
                # Before first transition, so use the default offset.
                offset = self._default_transition_type.utc_offset
                unix_time = (dt - datetime(1970, 1, 1)).total_seconds() - offset
            else:
                # tr.pre_time < dt < tr.time
                # Skipped time
                unix_time = tr.unix_time - (tr.pre_time - dt).total_seconds()
        elif tr == end:
            if tr.pre_time < dt:
                # After the last transition.
                unix_time = tr.unix_time + (dt - tr.time).total_seconds()
            else:
                # tr.time <= dt <= tr.pre_time
                # Repeated time
                unix_time = tr.unix_time + (dt - tr.time).total_seconds()
        else:
            if tr.pre_time <= dt < tr.time:
                # tr.pre_time <= dt < tr.time
                # Skipped time
                unix_time = tr.unix_time - (tr.pre_time - dt).total_seconds()
            elif tr.time <= dt <= tr.pre_time:
                # tr.time <= dt <= tr.pre_time
                # Repeated time
                unix_time = tr.unix_time + (dt - tr.time).total_seconds()
            else:
                # In between transitions
                # The actual transition type is the previous transition one

                # Fix for negative microseconds for negative timestamps
                diff = (dt - tr.pre_time).total_seconds()
                if -1 < diff < 0 and tr.unix_time < 0:
                    diff -= 1

                unix_time = tr.unix_time + diff

                transition_type = tr.pre_transition_type

        return self._to_local_time(unix_time, transition_type, offset)

    def _convert(self, dt):
        """
        Converts a timezone-aware datetime to local time.

        :param dt: The datetime to convert.
        :type dt: datetime
        """
        # if tzinfo is not set, something wrong happened
        if dt.tzinfo is None:
            raise ValueError(
                'A datetime without a tzinfo cannot be converted. '
                'Use _normalize() instead.'
            )

        unix_time = self._get_timestamp(dt)

        if not self._transitions:
            transition_type = self._default_transition_type
        else:
            idx = max(0, bisect_right(self._transitions, unix_time) - 1)
            tr = self._transitions[idx]
            transition_type = tr.transition_type

        return self._to_local_time(unix_time, transition_type)

    def _to_local_time(self, unix_time, transition_type, offset=None):
        local_time = Breakdown.local_time(
            unix_time,
            transition_type
        )

        tzinfo = TimezoneInfo(
            self,
            offset if offset is not None else transition_type.utc_offset,
            transition_type.is_dst,
            transition_type.abbrev
        )

        return datetime(
            local_time.year,
            local_time.month,
            local_time.day,
            local_time.hour,
            local_time.minute,
            local_time.second,
            local_time.microsecond,
            tzinfo=tzinfo
        )

    def _get_timestamp(self, dt):
        if hasattr(dt, 'float_timestamp'):
            return dt.float_timestamp

        if dt.tzinfo is None:
            t = _time.mktime((dt.year, dt.month, dt.day,
                              dt.hour, dt.minute, dt.second,
                              -1, -1, -1)) + dt.microsecond / 1e6

        else:
            t = (dt - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds()

        if dt.microsecond > 0 and t < 0:
            t -= 1

        return t

    def __repr__(self):
        return '<Timezone [{}]>'.format(self._name)
    
    
class FixedTimezone(Timezone):
    """
    A timezone that has a fixed offset to UTC.
    """
    
    def __init__(self, offset):
        """
        :param offset: offset to UTC in seconds.
        :type offset: int
        """
        sign = '-' if offset < 0 else '+'

        minutes = offset / 60
        hour, minute = divmod(abs(int(minutes)), 60)

        name = '{0}{1:02d}:{2:02d}'.format(sign, hour, minute)

        transition_type = TransitionType(int(offset), False, '')
        
        super(FixedTimezone, self).__init__(name, [], [], transition_type)


class _UTC(Timezone):

    def __init__(self):
        super(_UTC, self).__init__('UTC', [], [], TransitionType(0, False, 'GMT'))

        self._tzinfo = TimezoneInfo(self, 0, False, 'UTC')

    @property
    def tzinfo(self):
        return self._tzinfo

UTCTimezone = _UTC()
UTC = UTCTimezone.tzinfo