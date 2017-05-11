from __future__ import print_function

import sys


def lines_in(text, mfunc, *expected_lines):
    """Test that `*expected_lines` occur in order in the lines of `text`.

    Arguments:
        text (str): The text to find *expected_lines in
        mfunc (callable(str) -> str): Called from every line in text and every str (non re) in expected_lines.
            Can be used to modify the each str before comparison.
        *expected_lines (str, RegexObject (hasattr `match`) or sequence): For each `expected_line` in expected_lines:
            If an expected_line is a tuple or a list, any item in the sequence is handled as an individual
            expected_line, which may be matched in any order, but not out of order with the surrounding expected_lines,
            as described below:

            If `expected_line` has a match method it is called and must return True for a line in `text`.
            Otherwise, if the `expected_line` starts with '^', a line in `text` must start with `expected_line[1:]`
            Otherwise `expected line` must simply occur in a line in `text`

    Return (bool): True if lines found in order, else False
    """

    def _check_match(expected, line):
        expected = mfunc(expected) if mfunc and not hasattr(expected, 'match') else expected

        if hasattr(expected, 'match'):
            if expected.match(line):
                return True
            return False

        if expected.startswith('^'):
            if line.startswith(expected[1:]):
                return True
            return False

        if expected in line:
            return True

        return False

    matched_lines = []
    def _report_failure(expected):
        num_matched = len(matched_lines)
        if num_matched:
            matched = '\n\nMatched {num} lines:\n\n{lines}'.format(num=num_matched, lines='\n'.join(matched_lines))
        else:
            matched = '\n\nNo lines matched.' + " (Empty text)" if not text else ''

        if hasattr(expected, 'match'):
            print(matched, "\n\nThe regex:\n\n", expected.pattern, "\n\n    --- NOT MATCHED or OUT OF ORDER in ---\n\n", text, file=sys.stderr)
            return False

        if expected.startswith('^'):
            print(matched, "\n\nThe text:\n\n", expected[1:], "\n\n    --- NOT FOUND, OUT OF ORDER or NOT AT START OF LINE in ---\n\n", text, file=sys.stderr)
            return False

        print(matched, "\n\nThe text:\n\n", expected, "\n\n    --- NOT FOUND OR OUT OF ORDER IN ---\n\n", text, file=sys.stderr)
        return False

    max_index = len(expected_lines)
    index = 0

    for line in text.split('\n'):
        line = mfunc(line) if mfunc else line
        expected = expected_lines[index]

        if isinstance(expected, (tuple, list)):
            new_expected = []
            for unordered_expected in expected:
                if _check_match(unordered_expected, line):
                    matched_lines.append(line)
                    continue
                new_expected.append(unordered_expected)
            expected_lines[index] = new_expected if len(new_expected) > 1 else new_expected[0]
            continue

        if _check_match(expected, line):
            index += 1
            if index == max_index:
                return True
            matched_lines.append(line)

    if isinstance(expected, (tuple, list)):
        for expected in new_expected:
            # TODO: only reports first element
            return _report_failure(expected)

    return _report_failure(expected)
