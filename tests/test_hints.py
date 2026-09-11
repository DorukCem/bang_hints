"""Exact-match tests for the hint message pipeline.

Target: _bang_hints_resolve <lbuffer> <rbuffer>
  stdout = inner hint lines (newline-joined, NO box/border)
  exit 0 = hint applies, exit 1 = no hint.

Box/border, $COLUMNS truncation, and zle -M plumbing are display sugar
and are intentionally NOT asserted here.
"""

import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent / "bang-hints.plugin.zsh"


def resolve(lbuffer: str = "", rbuffer: str = "") -> tuple[str, int]:
    """Run the pure resolver in zsh. Buffers travel via env (no quoting hell)."""
    script = (
        'source "$PLUGIN_PATH"; '
        '_bang_hints_resolve "$BH_LBUFFER" "$BH_RBUFFER"'
    )
    proc = subprocess.run(
        ["zsh", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        env={
            "PLUGIN_PATH": str(PLUGIN),
            "BH_LBUFFER": lbuffer,
            "BH_RBUFFER": rbuffer,
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    )
    assert proc.stderr == "", f"unexpected zsh stderr for {lbuffer!r}: {proc.stderr}"
    return proc.stdout, proc.returncode


def check(lbuffer, rbuffer, expected):
    out, rc = resolve(lbuffer, rbuffer)
    if expected is None:
        assert rc == 1, f"[{lbuffer!r}] expected no hint, got: {out!r}"
        assert out == "", f"[{lbuffer!r}] expected empty stdout, got: {out!r}"
    else:
        assert rc == 0, f"[{lbuffer!r}] expected hint, got rc=1"
        assert out == expected, f"[{lbuffer!r}]\nexpected: {expected!r}\ngot:      {out!r}"


BASE_MENU = (
    "History expansion\n"
    "\n"
    "!!     previous command\n"
    "!$     last argument\n"
    "!^     first argument\n"
    "!*     all arguments\n"
    "!-n    n commands ago\n"
    "!foo   last command: foo\n"
    "!?foo  command containing\n"
)

MODIFIERS_MENU = (
    "Modifiers & Designators\n"
    "\n"
    ":0-9   nth argument\n"
    ":^ $ * first/last/all args\n"
    ":p     print without running\n"
    ":h :t  keep head / tail\n"
    ":r :e  remove / keep ext\n"
    ":s/x/y substitute x with y\n"
    ":g     apply globally\n"
)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # free text
        ("!foo", "", "Matches most recent command starting with 'foo'\n"),
        ("!foo-bar_1", "", "Matches most recent command starting with 'foo-bar_1'\n"),
        ("echo !foo", "", "Matches most recent command starting with 'foo'\n"),
        ("!fo", "o", "Matches most recent command starting with 'foo'\n"),
        # closed events
        ("!!", "", "!! → previous command\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!$", "", "!$ → last argument of previous command\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!^", "", "!^ → first argument of previous command\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!*", "", "!* → all arguments of previous command\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!#", "", "!# → current command line typed so far\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!-2", "", "!-2 → 2 commands ago\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!-10", "", "!-10 → 10 commands ago\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!123", "", "!123 → command #123\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("echo !!", "", "!! → previous command\n\n[ : for modifiers, Space/Enter to use ]\n"),
        # search
        ("!?foo", "", "Matches command containing this text\nClose search with ?\n"),
        ("!?foo?", "", "search closed\n\n[ : for modifiers, Space/Enter to use ]\n"),
        ("!?foo?:p", "", "print command without executing\n\n[ : for more, Space/Enter to run ]\n"),
        # pending
        ("!-", "", "Pending: !-n\nType a digit → n commands ago\n"),
        # menus
        ("!", "", BASE_MENU),
        ("!!:", "", MODIFIERS_MENU),
        # modifiers / word designators
        ("!!:p", "", "print command without executing\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:h", "", "keep head (remove tail)\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:1", "", "word designator 1 selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:1-3", "", "word designator 1-3 selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:^", "", "first argument selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!$", "", "last argument selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!*", "", "all arguments selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:s", "", "Substitute\nNext character sets your delimiter\n"),
        ("!!:s/a", "", "Typing pattern to match\nEnds at /\n"),
        ("!!:s/a/b", "", "Typing replacement\nEnds at /\n"),
        ("!!:s/a/b/", "", "substitution complete\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:s#a#b#", "", "substitution complete\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:g", "", "apply next modifier globally\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:q", "", "modifier q applied\n\n[ : for more, Space/Enter to run ]\n"),
        ("!-2:p", "", "print command without executing\n\n[ : for more, Space/Enter to run ]\n"),
        # no hint cases
        ("", "", None),
        ("a", "", None),
        ("ls", "", None),
        ("echo hi", "", None),
        ("!@", "", None),
        ("!-n", "", None),
        ("!-foo", "", None),
        ("!!:z", "", None),
        ("!!foo", "", None),
        ("\\!", "", None),
        ("echo \\!!", "", None),
        ("!!", "foo", None),  # full word !!foo is invalid; cursor mid-line
    ],
)
def test_resolve(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)
