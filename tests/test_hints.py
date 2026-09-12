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
    script = 'source "$PLUGIN_PATH"; _bang_hints_resolve "$BH_LBUFFER" "$BH_RBUFFER"'
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
        assert out == expected, (
            f"[{lbuffer!r}]\nexpected: {expected!r}\ngot:      {out!r}"
        )


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
    "!:     word designator (prev event)\n"
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
        (
            "!!",
            "",
            "!! → previous command\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "!$",
            "",
            "!$ → last argument of previous command\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "!^",
            "",
            "!^ → first argument of previous command\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "!*",
            "",
            "!* → all arguments of previous command\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "!#",
            "",
            "!# → current command line typed so far\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "!-2",
            "",
            "!-2 → 2 commands ago\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "!-10",
            "",
            "!-10 → 10 commands ago\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "!123",
            "",
            "!123 → command #123\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        (
            "echo !!",
            "",
            "!! → previous command\n\n[ : for modifiers, Space/Enter to use ]\n",
        ),
        # search
        ("!?foo", "", "Matches command containing this text\nClose search with ?\n"),
        ("!?foo?", "", "search closed\n\n[ : for modifiers, Space/Enter to use ]\n"),
        (
            "!?foo?:p",
            "",
            "print command without executing\n\n[ : for more, Space/Enter to run ]\n",
        ),
        # pending
        ("!-", "", "Pending: !-n\nType a digit → n commands ago\n"),
        # menus
        ("!", "", BASE_MENU),
        ("!!:", "", MODIFIERS_MENU),
        # modifiers / word designators
        (
            "!!:p",
            "",
            "print command without executing\n\n[ : for more, Space/Enter to run ]\n",
        ),
        ("!!:h", "", "keep head (remove tail)\n\n[ : for more, Space/Enter to run ]\n"),
        (
            "!!:1",
            "",
            "word designator 1 selected\n\n[ : for more, Space/Enter to run ]\n",
        ),
        (
            "!!:1-3",
            "",
            "word designator 1-3 selected\n\n[ : for more, Space/Enter to run ]\n",
        ),
        ("!!:^", "", "first argument selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!$", "", "last argument selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!*", "", "all arguments selected\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:s", "", "Substitute\nNext character sets your delimiter\n"),
        ("!!:s/a", "", "'a' → ?\nEnds at /\n"),
        ("!!:s/a/b", "", "'a' → 'b'\nEnds at /\n"),
        ("!!:s/a/b/", "", "'a' → 'b'\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:s#a#b#", "", "'a' → 'b'\n\n[ : for more, Space/Enter to run ]\n"),
        (
            "!!:gs/a/b/",
            "",
            "globally: 'a' → 'b'\n\n[ : for more, Space/Enter to run ]\n",
        ),
        ("!!:s/", "", "'' → ?\nEnds at /\n"),
        ("!!:s//bar/", "", "'' → 'bar'\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:s/foo//", "", "'foo' → ''\n\n[ : for more, Space/Enter to run ]\n"),
        ("!!:s/a\\/b/c/", "", "'a\\/b' → 'c'\n\n[ : for more, Space/Enter to run ]\n"),
        (
            "!!:g",
            "",
            "apply next modifier globally\n\n[ : for more, Space/Enter to run ]\n",
        ),
        ("!!:q", "", "modifier q applied\n\n[ : for more, Space/Enter to run ]\n"),
        (
            "!-2:p",
            "",
            "print command without executing\n\n[ : for more, Space/Enter to run ]\n",
        ),
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


CLOSED_SUFFIX = "\n\n[ : for modifiers, Space/Enter to use ]\n"
MORE_SUFFIX = "\n\n[ : for more, Space/Enter to run ]\n"


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # --- Event designators: canonical
        ("!4", "", "!4 → command #4" + CLOSED_SUFFIX),
        ("!10", "", "!10 → command #10" + CLOSED_SUFFIX),
        ("!356", "", "!356 → command #356" + CLOSED_SUFFIX),
        ("!467", "", "!467 → command #467" + CLOSED_SUFFIX),
        ("!-1", "", "!-1 → 1 commands ago" + CLOSED_SUFFIX),  # synonym for !!
        ("!-2", "", "!-2 → 2 commands ago" + CLOSED_SUFFIX),
        ("!-3", "", "!-3 → 3 commands ago" + CLOSED_SUFFIX),
        ("!ps", "", "Matches most recent command starting with 'ps'\n"),
        ("!git", "", "Matches most recent command starting with 'git'\n"),
        ("!cp", "", "Matches most recent command starting with 'cp'\n"),
        ("!tar", "", "Matches most recent command starting with 'tar'\n"),
        ("!vim", "", "Matches most recent command starting with 'vim'\n"),
        ("!ssh", "", "Matches most recent command starting with 'ssh'\n"),
        ("!cd", "", "Matches most recent command starting with 'cd'\n"),
        ("!ls", "", "Matches most recent command starting with 'ls'\n"),
        ("!sudo", "", "Matches most recent command starting with 'sudo'\n"),
        ("!?apache", "", "Matches command containing this text\nClose search with ?\n"),
        ("!?apache?", "", "search closed" + CLOSED_SUFFIX),
        ("!?ls?", "", "search closed" + CLOSED_SUFFIX),
        ("!?string?", "", "search closed" + CLOSED_SUFFIX),
        ("!!:s/ls/cat/", "", "'ls' → 'cat'" + MORE_SUFFIX),
        # --- !-1 / !! equivalence, sudo !! idiom context ---
        ("sudo !!", "", "!! → previous command" + CLOSED_SUFFIX),
        ("sudo !-1", "", "!-1 → 1 commands ago" + CLOSED_SUFFIX),
    ],
)
def test_events_canonical(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # --- Bare eventless refs
        ("!:0", "", "word designator 0 selected" + MORE_SUFFIX),
        ("!:1", "", "word designator 1 selected" + MORE_SUFFIX),
        ("!:$", "", "last argument selected" + MORE_SUFFIX),
        ("!:*", "", "all arguments selected" + MORE_SUFFIX),
        ("!:^", "", "first argument selected" + MORE_SUFFIX),
        ("!:%", "", "matched word selected" + MORE_SUFFIX),
        ("!{ls}", "", "Matches most recent command starting with 'ls'\n"),
        ("!{foo}bar", "", "Matches most recent command starting with 'foo'\n"),
        ("!{12}", "", "!12 → command #12" + CLOSED_SUFFIX),
        ("!{cp}", "", "Matches most recent command starting with 'cp'\n"),
        ("!=", "", None),
        ("!(", "", None),
        ("! ", "", None),
        ("echo ! =", "", None),
    ],
)
def test_events_bare_brace_inhibit(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # --- Word designators with event
        ("!!:0", "", "word designator 0 selected" + MORE_SUFFIX),
        ("!!:1", "", "word designator 1 selected" + MORE_SUFFIX),
        ("!!:2", "", "word designator 2 selected" + MORE_SUFFIX),
        ("!cp:^", "", "first argument selected" + MORE_SUFFIX),
        ("!!:^", "", "first argument selected" + MORE_SUFFIX),
        ("!cp:$", "", "last argument selected" + MORE_SUFFIX),
        ("!!:$", "", "last argument selected" + MORE_SUFFIX),
        ("!tar:2", "", "word designator 2 selected" + MORE_SUFFIX),
        ("!cp:*", "", "all arguments selected" + MORE_SUFFIX),
        ("!!:*", "", "all arguments selected" + MORE_SUFFIX),
        ("!-2:*", "", "all arguments selected" + MORE_SUFFIX),
        ("!-3:$", "", "last argument selected" + MORE_SUFFIX),
        ("!tar:2-$", "", "word designator 2-$ selected" + MORE_SUFFIX),
        ("!!:2*", "", "word designator 2* selected" + MORE_SUFFIX),
        ("!!:2-$", "", "word designator 2-$ selected" + MORE_SUFFIX),
        ("!!:2-", "", "word designator 2- selected" + MORE_SUFFIX),
        ("!tar:3-5", "", "word designator 3-5 selected" + MORE_SUFFIX),
        ("!!:3-$", "", "word designator 3-$ selected" + MORE_SUFFIX),
        ("!!:0-1", "", "word designator 0-1 selected" + MORE_SUFFIX),
        ("!!:1-$", "", "word designator 1-$ selected" + MORE_SUFFIX),
        ("!tar:2-", "", "word designator 2- selected" + MORE_SUFFIX),  # omit last
        (
            "!-2;!-1",
            "",
            "!-1 → 1 commands ago" + CLOSED_SUFFIX,
        ),  # cursor at end: current word is !-1
        # colon-less forms (may omit : before ^ $ * - %)
        ("!!^", "", "first argument selected" + MORE_SUFFIX),
        ("!!$", "", "last argument selected" + MORE_SUFFIX),
        ("!!*", "", "all arguments selected" + MORE_SUFFIX),
        ("!cp:2", "", "word designator 2 selected" + MORE_SUFFIX),
        ("ls -l !cp:^", "", "first argument selected" + MORE_SUFFIX),
        ("ls -l !cp:$", "", "last argument selected" + MORE_SUFFIX),
        ("ls -l !tar:2", "", "word designator 2 selected" + MORE_SUFFIX),
        ("ls -l !cp:*", "", "all arguments selected" + MORE_SUFFIX),
        ("!?apache?:%", "", "matched word selected" + MORE_SUFFIX),
    ],
)
def test_word_designators(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # --- Path modifiers :h :t :r :e + chains (geekstuff #10-12, redhat blog) ---
        ("!!:$:h", "", "keep head (remove tail)" + MORE_SUFFIX),
        ("!!:$:t", "", "keep tail (remove head)" + MORE_SUFFIX),
        ("!!:$:r", "", "remove extension" + MORE_SUFFIX),
        ("!!:2:r", "", "remove extension" + MORE_SUFFIX),
        ("!!:2:e", "", "keep extension only" + MORE_SUFFIX),
        ("!!^:h", "", "keep head (remove tail)" + MORE_SUFFIX),
        ("!!^:t", "", "keep tail (remove head)" + MORE_SUFFIX),
        ("ls -l !!:$:h", "", "keep head (remove tail)" + MORE_SUFFIX),
        ("ls -l !!:$:t", "", "keep tail (remove head)" + MORE_SUFFIX),
        ("ls -l !!:$:r", "", "remove extension" + MORE_SUFFIX),
        ("!-1:$:r", "", "remove extension" + MORE_SUFFIX),  # tarball -> dirname
        ("cd !-1:$:r", "", "remove extension" + MORE_SUFFIX),
        (
            "tar cvfz new-file.tar !tar:3-:p",
            "",
            "print command without executing" + MORE_SUFFIX,
        ),
        # --- Quoting/case/path-resolve modifiers
        ("!!:q", "", "modifier q applied" + MORE_SUFFIX),
        ("!!:x", "", "modifier x applied" + MORE_SUFFIX),
        ("!!:c", "", "modifier c applied" + MORE_SUFFIX),
        ("!-2:*:q", "", "modifier q applied" + MORE_SUFFIX),  # cheat-sheet quoting
        ("!!:a", "", "modifier a applied" + MORE_SUFFIX),
        ("!!:A", "", "modifier A applied" + MORE_SUFFIX),
        ("!!:l", "", "modifier l applied" + MORE_SUFFIX),
        ("!!:u", "", "modifier u applied" + MORE_SUFFIX),
        ("!!:U", "", "modifier U applied" + MORE_SUFFIX),
        ("!!:P", "", "modifier P applied" + MORE_SUFFIX),
        ("!!:Q", "", "modifier Q applied" + MORE_SUFFIX),
        ("!!:G", "", "modifier G applied" + MORE_SUFFIX),
        # --- History-only :p dry-run
        ("!!:p", "", "print command without executing" + MORE_SUFFIX),
        ("!123:p", "", "print command without executing" + MORE_SUFFIX),
        ("!-32:0-:s/mv/trash/:p", "", "print command without executing" + MORE_SUFFIX),
        ("./!$:p", "", "print command without executing" + MORE_SUFFIX),
    ],
)
def test_modifiers_path_quoting(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        ("!!:s/apt/dnf/", "", "'apt' → 'dnf'" + MORE_SUFFIX),
        ("!-3:s/vi/emacs/", "", "'vi' → 'emacs'" + MORE_SUFFIX),
        ("!!:gs/password/passwd/", "", "globally: 'password' → 'passwd'" + MORE_SUFFIX),
        ("!!:gs/pip/pip3/", "", "globally: 'pip' → 'pip3'" + MORE_SUFFIX),
        ("!!:s/foo/bzz/", "", "'foo' → 'bzz'" + MORE_SUFFIX),
        ("!!:s/cd/gf/", "", "'cd' → 'gf'" + MORE_SUFFIX),  # SO 11927342
        ("!!:s/checkbox/radio/", "", "'checkbox' → 'radio'" + MORE_SUFFIX),
        ("!!:gs/checkbox/radio/", "", "globally: 'checkbox' → 'radio'" + MORE_SUFFIX),
        ("!-4:1-3:s/a/foo/", "", "'a' → 'foo'" + MORE_SUFFIX),
        ("!!:s#password#passwd#", "", "'password' → 'passwd'" + MORE_SUFFIX),
        ("!!:s#/a#b#", "", "'/a' → 'b'" + MORE_SUFFIX),
        # pending states
        ("!!:s", "", "Substitute\nNext character sets your delimiter\n"),
        ("!!:g", "", "apply next modifier globally" + MORE_SUFFIX),
    ],
)
def test_modifiers_substitution(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # --- !# current line so far
        ("!#", "", "!# → current command line typed so far" + CLOSED_SUFFIX),
        ("mkdir foo && cd !#:1", "", "word designator 1 selected" + MORE_SUFFIX),
        (
            "mkdir backup_download_directory && cd !#:1",
            "",
            "word designator 1 selected" + MORE_SUFFIX,
        ),
        ("./foo.sh bar; !#:s/bar/baz/", "", "'bar' → 'baz'" + MORE_SUFFIX),
        ("mv /a/b/c/d.txt !#:1", "", "word designator 1 selected" + MORE_SUFFIX),
        ("echo !#", "", "!# → current command line typed so far" + CLOSED_SUFFIX),
        ("!#:1", "", "word designator 1 selected" + MORE_SUFFIX),
        ("!#:s/bar/baz/", "", "'bar' → 'baz'" + MORE_SUFFIX),
        ("!#:$:h", "", "keep head (remove tail)" + MORE_SUFFIX),
    ],
)
def test_hash_current_line(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # --- Verbatim real-world idioms
        ("sudo !!", "", "!! → previous command" + CLOSED_SUFFIX),
        (
            "./!$",
            "",
            "!$ → last argument of previous command" + CLOSED_SUFFIX,
        ),
        (
            "cd !$",
            "",
            "!$ → last argument of previous command" + CLOSED_SUFFIX,
        ),
        (
            "emacs !*",
            "",
            "!* → all arguments of previous command" + CLOSED_SUFFIX,
        ),
        (
            "vim !*",
            "",
            "!* → all arguments of previous command" + CLOSED_SUFFIX,
        ),
        ("ls -l !!:^", "", "first argument selected" + MORE_SUFFIX),  # geekstuff #4
        (
            "ls -l !!:$",
            "",
            "last argument selected" + MORE_SUFFIX,
        ),
        ("ls -l !$", "", "!$ → last argument of previous command" + CLOSED_SUFFIX),
        ("cat !?apache?", "", "search closed" + CLOSED_SUFFIX),
        (
            "/usr/local/bin/!:0",
            "",
            "word designator 0 selected" + MORE_SUFFIX,
        ),
        ("!-2*:s/foo/bar/", "", "'foo' → 'bar'" + MORE_SUFFIX),
        (">>!$", "", "!$ → last argument of previous command" + CLOSED_SUFFIX),
        (
            "echo !!:3-$",
            "",
            "word designator 3-$ selected" + MORE_SUFFIX,
        ),
    ],
)
def test_realworld_idioms(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)


@pytest.mark.parametrize(
    "lbuffer,rbuffer,expected",
    [
        # --- Quoting / escaping (bash: only \\ and ' quote; zsh: also $'', not "") ---
        ("\\!", "", None),
        ("\\!!", "", None),
        ("echo \\!!", "", None),
        ("echo \\!$", "", None),
        # --- Cursor mid-line: full word defines validity ---
        ("!fo", "o", "Matches most recent command starting with 'foo'\n"),
        ("!!", "foo", None),
        ("!-", "2", "!-2 → 2 commands ago" + CLOSED_SUFFIX),
        ("!!:", "", MODIFIERS_MENU),
        # --- Invalid / no-hint
        ("", "", None),
        ("!@", "", None),
        ("!-n", "", None),
        ("!-foo", "", None),
        ("!!foo", "", None),
        ("!!:z", "", None),
        ("echo hi", "", None),
        ("ls", "", None),
    ],
)
def test_quoting_cursor_negatives(lbuffer, rbuffer, expected):
    check(lbuffer, rbuffer, expected)
