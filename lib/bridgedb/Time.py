# -*- coding: utf-8 ; test-case-name: bridgedb.test.test_Time -*-
#
# This file is part of BridgeDB, a Tor bridge distribution system.
#
# :authors: Nick Mathewson
# :copyright: (c) 2007-2014, The Tor Project, Inc.
# :license: see LICENSE for licensing information


"""This module implements functions for dividing time into chunks."""

import calendar
import time

from zope import interface
from zope.interface import implements

KNOWN_INTERVALS = [ "hour", "day", "week", "month" ]


class ISchedule(interface.Interface):
    """A ``Interface`` specification for a Schedule."""

    def intervalStart(when):
        """Set the start time of the current interval to **when**."""

    def getInterval(when=None):
        """Get the interval which includes an arbitrary **when**."""

    def nextIntervalStarts():
        """Get the start time for the next interval."""


class ScheduleBase(object):
    """Base class for all ``Schedule`` classes."""

    implements(ISchedule)

    def intervalStart(self, when):
        pass

    def getInterval(self, when=None):
        pass

    def nextIntervalStarts(self):
        pass


class IntervalSchedule(ScheduleBase):
    """An IntervalSchedule splits time into somewhat natural periods,
       based on hours, days, weeks, or months.
    """
    ## Fields:
    ##  itype -- one of "month", "day", "hour".
    ##  count -- how many of the units in itype belong to each period.
    def __init__(self, intervaltype, count):
        """Create a new IntervalSchedule.
            intervaltype -- one of month, week, day, hour.
            count -- how many of the units in intervaltype belong to each
                     period.
        """
        it = intervaltype.lower()
        if it.endswith("s"): it = it[:-1]
        if it not in KNOWN_INTERVALS:
            raise TypeError("What's a %s?"%it)
        assert count > 0
        if it == 'week':
            it = 'day'
            count *= 7
        self.itype = it
        self.count = count

    def intervalStart(self, when):
        """Return the time (as an int) of the start of the interval containing
           'when'."""
        if self.itype == 'month':
            # For months, we always start at the beginning of the month.
            tm = time.gmtime(when)
            n = tm.tm_year * 12 + tm.tm_mon - 1
            n -= (n % self.count)
            month = n%12 + 1
            return calendar.timegm((n//12, month, 1, 0, 0, 0))
        elif self.itype == 'day':
            # For days, we start at the beginning of a day.
            when -= when % (86400 * self.count)
            return when
        elif self.itype == 'hour':
            # For hours, we start at the beginning of an hour.
            when -= when % (3600 * self.count)
            return when
        else:
            assert False

    def getInterval(self, when):
        """Return a string representing the interval that contains the time
        **when**.

        >>> import calendar
        >>> from bridgedb.Time import IntervalSchedule
        >>> t = calendar.timegm((2007, 12, 12, 0, 0, 0))
        >>> I = IntervalSchedule('month', 1)
        >>> I.getInterval(t)
        '2007-12'

        :param int when: The time which we're trying to find the corresponding
                         interval for.
        :rtype: str
        :returns: A timestamp in the form ``YEAR-MONTH[-DAY[-HOUR]]``. It's
                  specificity depends on what type of interval we're
                  using. For example, if using ``"month"``, the return value
                  would be something like ``"2013-12"``.
        """
        if self.itype == 'month':
            tm = time.gmtime(when)
            n = tm.tm_year * 12 + tm.tm_mon - 1
            n -= (n % self.count)
            month = n%12 + 1
            return "%04d-%02d" % (n // 12, month)
        elif self.itype == 'day':
            when = self.intervalStart(when) + 7200 #slop
            tm = time.gmtime(when)
            return "%04d-%02d-%02d" % (tm.tm_year, tm.tm_mon, tm.tm_mday)
        elif self.itype == 'hour':
            when = self.intervalStart(when) + 120 #slop
            tm = time.gmtime(when)
            return "%04d-%02d-%02d %02d" % (tm.tm_year, tm.tm_mon, tm.tm_mday,
                                            tm.tm_hour)
        else:
            assert False

    def nextIntervalStarts(self, when):
        """Return the start time of the interval starting _after_ when."""
        if self.itype == 'month':
            tm = time.gmtime(when)
            n = tm.tm_year * 12 + tm.tm_mon - 1
            n -= (n % self.count)
            month = n%12 + 1
            tm = (n // 12, month+self.count, 1, 0,0,0)
            return calendar.timegm(tm)
        elif self.itype == 'day':
            return self.intervalStart(when) + 86400 * self.count
        elif self.itype == 'hour':
            return self.intervalStart(when) + 3600 * self.count

class NoSchedule(ScheduleBase):
    """A stub-implementation of Schedule that has only one period for
       all time."""
    def __init__(self):
        pass
    def intervalStart(self, when):
        return 0
    def getInterval(self, when):
        return "1970"
    def nextIntervalStarts(self, when):
        return 2147483647L # INT32_MAX

