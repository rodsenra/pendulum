import pytest
import pendulum

from datetime import datetime, date, time
from pendulum.helpers import precise_diff, parse_iso8601
from pendulum.tz.timezone import Timezone

from .conftest import assert_datetime, assert_date, assert_time


def test_precise_diff():
    dt1 = datetime(2003, 3, 1, 0, 0, 0)
    dt2 = datetime(2003, 1, 31, 23, 59, 59)

    diff = precise_diff(dt1, dt2)
    assert_diff(diff, months=-1, seconds=-1)

    diff = precise_diff(dt2, dt1)
    assert_diff(diff, months=1, seconds=1)

    dt1 = datetime(2012, 3, 1, 0, 0, 0)
    dt2 = datetime(2012, 1, 31, 23, 59, 59)

    diff = precise_diff(dt1, dt2)
    assert_diff(diff, months=-1, seconds=-1)

    diff = precise_diff(dt2, dt1)
    assert_diff(diff, months=1, seconds=1)

    dt1 = datetime(2001, 1, 1)
    dt2 = datetime(2003, 9, 17, 20, 54, 47, 282310)

    diff = precise_diff(dt1, dt2)
    assert_diff(
        diff,
        years=2, months=8, days=16,
        hours=20, minutes=54, seconds=47, microseconds=282310
    )

    dt1 = datetime(2017, 2, 17, 16, 5, 45, 123456)
    dt2 = datetime(2018, 2, 17, 16, 5, 45, 123256)

    diff = precise_diff(dt1, dt2)
    assert_diff(
        diff,
        months=11, days=30, hours=23, minutes=59, seconds=59, microseconds=999800
    )

    # DST
    tz = Timezone.load('America/Toronto')
    dt1 = tz.datetime(2017, 3, 7)
    dt2 = tz.datetime(2017, 3, 13)

    diff = precise_diff(dt1, dt2)
    assert_diff(
        diff,
        days=5, hours=23
    )


def test_parse_iso8601():
    if not parse_iso8601:
        pytest.skip('parse_iso8601 is only supported with C extensions.')

    from pendulum._extensions._helpers import TZFixedOffset

    # Date
    assert date(2016, 1, 1) == parse_iso8601('2016')
    assert date(2016, 10, 1) == parse_iso8601('2016-10')
    assert date(2016, 10, 6) == parse_iso8601('2016-10-06')
    assert date(2016, 10, 6) == parse_iso8601('20161006')

    # Time
    assert time(20, 16, 10, 0) == parse_iso8601('201610')

    # Datetime
    assert datetime(2016, 10, 6, 12, 34, 56, 123456) == parse_iso8601('2016-10-06T12:34:56.123456')
    assert datetime(2016, 10, 6, 12, 34, 56, 123000) == parse_iso8601('2016-10-06T12:34:56.123')
    assert datetime(2016, 10, 6, 12, 34, 56, 123) == parse_iso8601('2016-10-06T12:34:56.000123')
    assert datetime(2016, 10, 6, 12, 0, 0, 0) == parse_iso8601('2016-10-06T12')
    assert datetime(2016, 10, 6, 12, 34, 56, 0) == parse_iso8601('2016-10-06T123456')
    assert datetime(2016, 10, 6, 12, 34, 56, 123456) == parse_iso8601('2016-10-06T123456.123456')
    assert datetime(2016, 10, 6, 12, 34, 56, 123456) == parse_iso8601('20161006T123456.123456')
    assert datetime(2016, 10, 6, 12, 34, 56, 123456) == parse_iso8601('20161006 123456.123456')

    # Datetime with offset
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(19800))
        ==
        parse_iso8601('2016-10-06T12:34:56.123456+05:30')
    )
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(19800))
        ==
        parse_iso8601('2016-10-06T12:34:56.123456+0530')
    )
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(-19800))
        ==
        parse_iso8601('2016-10-06T12:34:56.123456-05:30')
    )
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(-19800))
        ==
        parse_iso8601('2016-10-06T12:34:56.123456-0530')
    )
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(18000))
        ==
        parse_iso8601('2016-10-06T12:34:56.123456+05')
    )
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(-18000))
        ==
        parse_iso8601('2016-10-06T12:34:56.123456-05')
    )
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(-18000))
        ==
        parse_iso8601('20161006T123456,123456-05')
    )
    assert (
        datetime(2016, 10, 6, 12, 34, 56, 123456, TZFixedOffset(+19800))
        ==
        parse_iso8601('2016-10-06T12:34:56.123456789+05:30')
    )

    # Ordinal date
    assert date(2012, 1, 7) == parse_iso8601('2012-007')
    assert date(2012, 1, 7) == parse_iso8601('2012007')
    assert date(2017, 3, 20) == parse_iso8601('2017-079')

    # Week date
    assert date(2012, 1, 30) == parse_iso8601('2012-W05')
    assert date(2008, 9, 27) == parse_iso8601('2008-W39-6')
    assert date(2010, 1, 3) == parse_iso8601('2009-W53-7')
    assert date(2008, 12, 29) == parse_iso8601('2009-W01-1')

    # Week date wth time
    assert datetime(2008, 9, 27, 9, 0, 0, 0) == parse_iso8601('2008-W39-6T09')

def test_parse_ios8601_invalid():
    if not parse_iso8601:
        pytest.skip('parse_iso8601 is only supported with C extensions.')

    # Invalid month
    with pytest.raises(ValueError):
        parse_iso8601('20161306T123456')

    # Invalid day
    with pytest.raises(ValueError):
        parse_iso8601('20161033T123456')

    # Invalid day for month
    with pytest.raises(ValueError):
        parse_iso8601('20161131T123456')

    # Invalid hour
    with pytest.raises(ValueError):
        parse_iso8601('20161006T243456')

    # Invalid minute
    with pytest.raises(ValueError):
        parse_iso8601('20161006T126056')

    # Invalid second
    with pytest.raises(ValueError):
        parse_iso8601('20161006T123460')

    # Extraneous separator
    with pytest.raises(ValueError):
        parse_iso8601('20140203 04:05:.123456')
    with pytest.raises(ValueError):
        parse_iso8601('2009-05-19 14:')

    # Invalid ordinal
    with pytest.raises(ValueError):
        parse_iso8601('2009367')
    with pytest.raises(ValueError):
        parse_iso8601('2009-367')
    with pytest.raises(ValueError):
        parse_iso8601('2015-366')
    with pytest.raises(ValueError):
        parse_iso8601('2015-000')

    # Invalid date
    with pytest.raises(ValueError):
        parse_iso8601('2009-')

    # Invalid time
    with pytest.raises(ValueError):
        parse_iso8601('2009-05-19T14:3924')
    with pytest.raises(ValueError):
        parse_iso8601('2010-02-18T16.5:23.35:48')
    with pytest.raises(ValueError):
        parse_iso8601('2010-02-18T16:23.35:48.45')
    with pytest.raises(ValueError):
        parse_iso8601('2010-02-18T16:23.33.600')

    # Invalid offset
    with pytest.raises(ValueError):
        parse_iso8601('2009-05-19 14:39:22+063')
    with pytest.raises(ValueError):
        parse_iso8601('2009-05-19 14:39:22+06a00')
    with pytest.raises(ValueError):
        parse_iso8601('2009-05-19 14:39:22+0:6:00')

    # Missing time separator
    with pytest.raises(ValueError):
        parse_iso8601('2009-05-1914:39')

    # Invalid week date
    with pytest.raises(ValueError):
        parse_iso8601('2012-W63')
    with pytest.raises(ValueError):
        parse_iso8601('2012-W12-9')
    with pytest.raises(ValueError):
        parse_iso8601('2012W12-3')  # Missing separator
    with pytest.raises(ValueError):
        parse_iso8601('2012-W123')  # Missing separator

def assert_diff(diff,
                years=0, months=0, days=0,
                hours=0, minutes=0, seconds=0, microseconds=0):
    assert diff.years == years
    assert diff.months == months
    assert diff.days == days
    assert diff.hours == hours
    assert diff.minutes == minutes
    assert diff.seconds == seconds
    assert diff.microseconds == microseconds


def test_test_now():
    now = pendulum.create(2000, 11, 10, 12, 34, 56, 123456)
    pendulum.set_test_now(now)

    assert pendulum.has_test_now()
    assert now == pendulum.get_test_now()
    assert now.date() == pendulum.date.today()
    assert now.time() == pendulum.time.now()

    assert_datetime(
        pendulum.datetime.now(),
        2000, 11, 10, 12, 34, 56, 123456
    )
    assert_date(
        pendulum.date.today(),
        2000, 11, 10
    )
    assert_time(
        pendulum.time.now(),
        12, 34, 56, 123456
    )

    pendulum.set_test_now()

    assert not pendulum.has_test_now()
    assert pendulum.get_test_now() is None


def test_formatter():
    dt = pendulum.create(2000, 11, 10, 12, 34, 56, 123456)
    pendulum.set_formatter('alternative')

    assert pendulum.get_formatter() is pendulum.FORMATTERS['alternative']

    assert (
        dt.format('YYYY-MM-DD HH:mm:ss.SSSSSSZZ')
        ==
        '2000-11-10 12:34:56.123456+00:00'
    )
    assert (
        dt.date().format('YYYY-MM-DD')
        ==
        '2000-11-10'
    )
    assert(
        dt.time().format('HH:mm:ss.SSSSSS')
        ==
        '12:34:56.123456'
    )

    pendulum.set_formatter()

    assert pendulum.get_formatter() is pendulum.FORMATTERS['classic']

    assert (
        dt.format('YYYY-MM-DD HH:mm:ss.SSSSSSZZ')
        ==
        'YYYY-MM-DD HH:mm:ss.SSSSSSZZ'
    )
    assert (
        dt.date().format('YYYY-MM-DD')
        ==
        'YYYY-MM-DD'
    )
    assert (
        dt.time().format('HH:mm:ss.SSSSSS')
        ==
        'HH:mm:ss.SSSSSS'
    )


def test_set_formatter_invalid():
    with pytest.raises(ValueError):
        pendulum.set_formatter('invalid')

def test_locale():
    dt = pendulum.create(2000, 11, 10, 12, 34, 56, 123456)
    pendulum.set_formatter('alternative')
    pendulum.set_locale('fr')

    assert pendulum.get_locale() == 'fr'

    assert dt.format('MMMM') == 'novembre'
    assert dt.date().format('MMMM') == 'novembre'


def test_set_locale_invalid():
    with pytest.raises(ValueError):
        pendulum.set_locale('invalid')

@pytest.mark.parametrize('locale', [
    'DE',
    'pt-BR',
    'pt-br',
    'PT-br',
    'PT-BR',
    'pt_br',
    'PT_BR',
    'PT_BR'
])
def test_set_locale_malformed_locale(locale):
    pendulum.set_locale(locale)

    pendulum.set_locale('en')
