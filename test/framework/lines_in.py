import sys


class _NotFoundException(Exception):
    pass


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

    text_lines = text.split('\n')
    max_line_index = len(text_lines)
    matched_lines = []

    def _check_match(expected, mline, line):
        expected = mfunc(expected) if mfunc and not hasattr(expected, 'match') else expected

        if hasattr(expected, 'match'):
            if expected.match(mline):
                matched_lines.append((line, mline))
                return True
            return False

        if expected.startswith('^'):
            if mline.startswith(expected[1:]):
                matched_lines.append((line, mline))
                return True
            return False

        if expected in mline:
            matched_lines.append((line, mline))
            return True

        return False

    def _report_failure(expected):
        num_matched = len(matched_lines)
        if num_matched:
            lines = []
            for line, mline in matched_lines:
                lines.append((line + ' (' + mline + ')') if line != mline else line)
            matched = "Matched {num} lines{mfunc_info}:\n\n{lines}".format(
                num=num_matched, mfunc_info=" ('mfunc' modified line in '()')" if mfunc else "", lines='\n'.join(lines))
        else:
            matched = 'No lines matched.' + " (Empty text)" if not text else ''

        raw_txt_msg = " (unmodified text, 'mfunc' not applied)" if mfunc else ''

        if hasattr(expected, 'match'):
            print('', matched, "The regex:", expected.pattern,
                  "--- NOT MATCHED or OUT OF ORDER in" + raw_txt_msg + " ---", text, file=sys.stderr, sep='\n\n')
            raise _NotFoundException()

        if expected.startswith('^'):
            expected = expected[1:]
            expinfo = expected + (" (" + mfunc(expected) + ")" if mfunc else "")
            print('', matched, "The text:", expinfo,
                  "--- NOT FOUND, OUT OF ORDER or NOT AT START OF LINE in" + raw_txt_msg + " ---", text, file=sys.stderr, sep='\n\n')
            raise _NotFoundException()

        expinfo = expected + (" (" + mfunc(expected) + ")" if mfunc else "")
        print('', matched, "The text:", expinfo,
              "--- NOT FOUND OR OUT OF ORDER IN" + raw_txt_msg + " ---", text, file=sys.stderr, sep='\n\n')
        raise _NotFoundException()

    def _ordered_lines_in(text_line_index, mfunc, expected_lines):
        max_expected_index = len(expected_lines)
        expected_index = 0

        while True:
            if expected_index == max_expected_index:
                return text_line_index
            expected = expected_lines[expected_index]

            if text_line_index == max_line_index:
                _report_failure(expected)

            if isinstance(expected, (tuple, list)):
                text_line_index = _unordered_lines_in(text_line_index, mfunc, expected)
                expected_index += 1
                continue

            line = text_lines[text_line_index]
            mline = mfunc(line) if mfunc else line
            if _check_match(expected, mline, line):
                expected_index += 1

            text_line_index += 1

    def _unordered_lines_in(text_line_index, mfunc, expected_lines):
        expected_lines = list(expected_lines)
        expected_index = 0

        while True:
            line = text_lines[text_line_index]
            mline = mfunc(line) if mfunc else line

            for expected_index, expected in enumerate(expected_lines):
                if isinstance(expected, (tuple, list)):
                    text_line_index = _ordered_lines_in(text_line_index, mfunc, expected)
                    del expected_lines[expected_index]
                    break

                if _check_match(expected, mline, line):
                    del expected_lines[expected_index]
                    break

            text_line_index += 1
            if not expected_lines:
                return text_line_index

            if text_line_index == max_line_index:
                _report_failure(expected)

    try:
        _ordered_lines_in(0, mfunc, expected_lines)
        return True
    except _NotFoundException:
        return False
