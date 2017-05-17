# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function
import os, re

import pytest

from ..lines_in import lines_in


_text = """
abcd1
bcde2
cdef3
defg4
efgh5
"""


def _no_output(capsys):
    sout, serr = capsys.readouterr()
    if sout or serr:
        return False
    return True


def _serr(capsys):
    sout, serr = capsys.readouterr()
    assert not sout
    return serr


def test_consecutive(capsys):
    assert lines_in(
        _text, None,
        'abcd1',
        'bcde2',
        'cdef3',
        'defg4',
        'efgh5',
    )
    assert _no_output(capsys)


def test_in_order(capsys):
    assert lines_in(
        _text, None,
        'abcd1',
        'cdef3',
        'efgh5',
    )
    assert _no_output(capsys)


def test_in_order_partial_line(capsys):
    assert lines_in(
        _text, None,
        'abc',
        'cde2',
        'fgh',
    )
    assert _no_output(capsys)


def test_in_order_start_line(capsys):
    assert lines_in(
        _text, None,
        '^abcd1',
        '^cdef3',
        '^efgh5',
    )
    assert _no_output(capsys)


def test_in_order_start_line_partial(capsys):
    assert lines_in(
        _text, None,
        '^ab',
        '^cde',
        '^efgh',
    )
    assert _no_output(capsys)


_not_in_order_expect_msg = """
Matched 1 lines:

cdef3

The text:

abcd1

--- NOT FOUND OR OUT OF ORDER IN ---


abcd1
bcde2
cdef3
defg4
efgh5
"""


def test_not_in_order(capsys):
    assert not lines_in(
        _text, None,
        'cdef3',
        'abcd1',
        'efgh5',
    )
    assert _not_in_order_expect_msg in _serr(capsys)


_not_in_order_partial_line_expect_msg = """
Matched 1 lines:

bcde2

The text:

abc

--- NOT FOUND OR OUT OF ORDER IN ---


abcd1
bcde2
cdef3
defg4
efgh5
"""

def test_not_in_order_partial_line(capsys):
    assert not lines_in(
        _text, None,
        'cde2',
        'abc',
        'fgh',
    )
    assert _not_in_order_partial_line_expect_msg in _serr(capsys)


_in_order_not_start_line_expect_msg = """
The text:

bcd1

--- NOT FOUND, OUT OF ORDER or NOT AT START OF LINE in ---


abcd1
bcde2
cdef3
defg4
efgh5
"""

def test_in_order_not_start_line(capsys):
    assert not lines_in(
        _text, None,
        '^bcd1',
        '^cdef3',
        '^efgh5',
    )
    assert _in_order_not_start_line_expect_msg in _serr(capsys)


def test_in_order_regex(capsys):
    assert lines_in(
        _text, None,
        re.compile('^ab.d1$'),
        re.compile('.*def3$'),
        re.compile('e.*5'),
    )
    assert _no_output(capsys)


_not_in_order_regex_expect_msg = """
Matched 1 lines:

cdef3

The regex:

^ab.d1$

--- NOT MATCHED or OUT OF ORDER in ---


abcd1
bcde2
cdef3
defg4
efgh5
"""

def test_not_in_order_regex(capsys):
    assert not lines_in(
        _text, None,
        re.compile('.*def3$'),
        re.compile('^ab.d1$'),
        re.compile('e.*5'),
    )
    assert _not_in_order_regex_expect_msg in _serr(capsys)


_not_matched_regex_expect_msg = """
The regex:

.*def7$

--- NOT MATCHED or OUT OF ORDER in ---


abcd1
bcde2
cdef3
defg4
efgh5
"""

def test_not_matched_regex(capsys):
    assert not lines_in(
        _text, None,
        re.compile('.*def7$'),
    )
    assert _not_matched_regex_expect_msg in _serr(capsys)


# TODO improved messages for 'no-text'
_not_matched_regex_no_text_expect_msg = """
No lines matched. (Empty text)

The regex:

.*def7$

--- NOT MATCHED or OUT OF ORDER in ---
"""

def test_not_matched_regex_no_text(capsys):
    assert not lines_in(
        '', None,
        re.compile('.*def7$'),
    )
    assert _not_matched_regex_no_text_expect_msg in _serr(capsys)


def test_unordered_matched(capsys):
    assert lines_in(
        _text, None,
        'abcd1', (
            'bcde2',
            'cdef3',
            'defg4',
        ),
        'efgh5'
    )

    assert lines_in(
        _text, None,
        'abcd1', (
            'defg4',
            'bcde2',
            'cdef3',
        ),
        'efgh5'
    )

    assert lines_in(
        _text, None,
        'abcd1', (
            'defg4',
            'cdef3',
            'efgh5',
        ),
    )

    assert _no_output(capsys)


def test_unordered_not_matched(capsys):
    assert not lines_in(
        _text, None,
        'abcd1', (
            'bcde2',
            'cdef3',
            'defg17',
        ),
        'efgh5'
    )

    assert not lines_in(
        _text, None,
        '^bcd1', (
            'defg4',
            'bcde2',
            'cdef3',
        ),
        'efgh5'
    )

    assert not lines_in(
        _text, None,
        'abcd1', (
            re.compile('efg4'),
            'cdef3',
            'efgh5',
        ),
    )

    assert not lines_in(
        _text, None,
        (
            re.compile('efg4'),
            'cdef3',
            'efgh5',
        ),
    )


def test_unordered_multiple_not_matched(capsys):
    assert not lines_in(
        _text, None,
        'abcd1', (
            'bcde2',
            'defg4',
            'cdef3',
        ), (
            'bcde2',
            'cdef33',
            'defg4',
        ),
        'efgh5'
    )

    assert not lines_in(
        _text, None,
        'abcd1', (
            'bcde2',
            'defg4',
            'cdef3',
        ), (
            'bcde2',
            'cdef3',
            'defg44',
        ),
    )


_repeat_text = """
XX
XX
"""

def test_in_order_repeat(capsys):
    assert lines_in(
        _repeat_text, None,
        "XX",
        "XX",
    )
    assert _no_output(capsys)


def test_unordered_repeat(capsys):
    assert lines_in(
        _repeat_text, None, (
            "XX",
            "XX",
        ),
    )
    assert _no_output(capsys)


def test_in_order_repeat_exhausted(capsys):
    assert not lines_in(
        _repeat_text, None,
        "XX",
        "XX",
        "XX",
    )


def test_unordered_repeat_exhausted(capsys):
    assert not lines_in(
        _repeat_text, None, (
            "XX",
            "XX",
            "XX",
        ),
    )


def test_in_order_unordered_repeat_exhausted(capsys):
    assert not lines_in(
        _repeat_text, None, (
            "XX",
            "XX",
        ),
        "XX",
    )


_long_text = """
abcd1
bcde2
cdef3
defg4
efgh5
6efgh
7efgh
8efgh
"""

def test_multi_nested(capsys):
    assert lines_in(
        _long_text, None,
        "abcd1", (
            "cdef3",
            "bcde2", (
                "defg4",
                "efgh5", (
                    '8efgh',
                    '7efgh',
                ),
            ),
        ),
    )
    assert _no_output(capsys)


def test_multi_nested_not_found():
    assert not lines_in(
        _long_text, None,
        "abcd1", (
            "cdef3",
            "bcde2", (
                "defg17",
                "efgh5", (
                    '8efgh',
                    '7efgh',
                ),
            ),
        ),
    )


def test_func_regex(capsys):
    def repl(line):
        return line.replace('bc', 'yy').replace('h5', 'yy')

    assert lines_in(
        _text, repl,
        re.compile('^ayyd1$'),
        'bcde2',
        'yy',
    )
    assert _no_output(capsys)


_func_regex_not_found_expect_msg = """
Matched 2 lines ('mfunc' modified line in '()'):

abcd1 (ayyd1)
bcde2 (yyde2)

The text:

yyz (yyz)

--- NOT FOUND OR OUT OF ORDER IN (unmodified text, 'mfunc' not applied) ---


abcd1
bcde2
cdef3
defg4
efgh5
"""

def test_func_regex_not_found(capsys):
    def repl(line):
        return line.replace('bc', 'yy').replace('h5', 'yy')

    assert not lines_in(
        _text, repl,
        re.compile('^ayyd1$'),
        'bcde2',
        'yyz',
    )
    assert _func_regex_not_found_expect_msg in _serr(capsys)
