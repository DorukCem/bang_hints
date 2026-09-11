# bang-hints.plugin.zsh
#
# Provides interactive hints for Zsh history expansion (!).
# Driven by zle-line-pre-redraw to seamlessly handle typing, backspace, and pastes.
# Supports v2 scope: modifiers, word designators, and substitution tracking.

autoload -Uz add-zle-hook-widget

# Tracks whether a hint is currently displayed, so we only call `zle -M ''`
# when there is actually something to clear. Calling `zle -M ''`
# unconditionally reserves the message line (visible as a stray space).
# Preserve across re-source so a visible hint can still be cleared.
(( ${+_bang_hints_shown} )) || typeset -g _bang_hints_shown=0

_bang_hints_show() {
    emulate -L zsh
    _bang_hints_shown=1
    zle -M "$1"
}

_bang_hints_clear() {
    emulate -L zsh
    (( _bang_hints_shown )) || return 0
    _bang_hints_shown=0
    zle -M ''
}

# Helper function to draw a clean ASCII/Unicode box around multiple lines of text.
# Long lines (e.g. a huge !foo) are truncated with … so the box never
# exceeds the terminal width.
_bang_hints_draw_box() {
    emulate -L zsh
    local term_w=${COLUMNS:-80}
    (( term_w > 0 )) 2>/dev/null || term_w=80
    local max_text=$(( term_w - 10 ))
    (( max_text < 20 )) && max_text=20
    local -a lines=()
    local t
    for t in "$@"; do
        if (( ${#t} > max_text )); then
            lines+=("${t[1,max_text-1]}…")
        else
            lines+=("$t")
        fi
    done
    local max_len=0
    local line
    
    # Find the longest line to size the box
    for line in "${lines[@]}"; do
        (( ${#line} > max_len )) && max_len=${#line}
    done
    
    # Native Zsh padding: (pl:width::string:) generates the horizontal border
    local border=${(pl:$((max_len + 2))::─:)}
    local NL=$'\n'
    local out="   ┌${border}┐${NL}"
    
    # Build each line with right-padding (r:max_len:)
    for line in "${lines[@]}"; do
        local padded=${(r:$max_len:)line}
        out+="   │ ${padded} │${NL}"
    done
    
    out+="   └${border}┘"
    
    # Print raw, avoiding any shell escape interpretations.
    # builtin: immune to a user `alias print=...` defined before sourcing.
    builtin print -r -- "$out"
}

# Pure resolver: the testable pipeline.
# Usage: _bang_hints_resolve "$lbuffer" "$rbuffer"
# Prints the inner hint lines (\n-joined, NO box/border) to stdout,
# exits 0 when a hint applies, 1 when none applies.
# No zle, no global state, no $COLUMNS dependence.
_bang_hints_resolve() {
    emulate -L zsh
    # extendedglob is required for (#b) backreference matching
    setopt extendedglob
    # Don't clobber a caller's $match (e.g. completion code interrupted by redraw)
    local -a match mbegin mend
    local MATCH MBEGIN MEND

    # 1. Isolate the current word being typed, including the part after
    # the cursor (rbuffer arg) up to the next separator, so mid-line cursor
    # positions describe the full word (e.g. LBUFFER="!!" RBUFFER="foo").
    local _bh_lbuffer="${1:-}"
    local _bh_rbuffer="${2:-}"
    local _bh_after="${_bh_rbuffer}"
    _bh_after="${_bh_after%%[ $'\t'|<>&;]*}"
    local current_word="${_bh_lbuffer##*[ $'\t'|<>&;]}${_bh_after}"
    
    local bang_idx=${current_word[(i)!]}
    if (( bang_idx == 0 || bang_idx > ${#current_word} )); then
        return 1
    fi
    
    local prefix=${current_word[1,bang_idx-1]}
    if [[ "$prefix" == *\\ ]]; then
        return 1
    fi

    local rem="${current_word[bang_idx,-1]}"
    local ev_hint=""
    local is_free_text=0
    
    # ---------------------------------------------------------
    # PART 1: Parse the Base Event Designator (e.g. !!, !foo, !-2)
    # ---------------------------------------------------------
    if [[ "$rem" == (#b)(!\?([^\?]#)\?)(*) ]]; then
        ev_hint="search closed"
        rem="${match[3]}"
    elif [[ "$rem" == (#b)(!\?*) ]]; then
        builtin print -r -- "Matches command containing this text
Close search with ?"
        return 0
    elif [[ "$rem" == (#b)(![\!\$\*#\^])(*) ]]; then
        case "${match[1]}" in
            "!!") ev_hint="!! → previous command" ;;
            "!\$") ev_hint="!\$ → last argument of previous command" ;;
            "!^") ev_hint="!^ → first argument of previous command" ;;
            "!*") ev_hint="!* → all arguments of previous command" ;;
            "!#") ev_hint="!# → current command line typed so far" ;;
        esac
        rem="${match[2]}"
    elif [[ "$rem" == (#b)(!-[0-9]##)(*) ]]; then
        ev_hint="${match[1]} → ${match[1]#!-} commands ago"
        rem="${match[2]}"
    elif [[ "$rem" == "!"- ]]; then
        builtin print -r -- "Pending: !-n
Type a digit → n commands ago"
        return 0
    elif [[ "$rem" == !-* ]]; then
        # !- followed by non-digit (e.g. !-n, !-foo) is invalid, not !foo
        return 1
    elif [[ "$rem" == (#b)(![0-9]##)(*) ]]; then
        ev_hint="${match[1]} → command #${match[1]#!}"
        rem="${match[2]}"
    elif [[ "$rem" == "!" ]]; then
        # Multiline base menu
        builtin print -r -- "History expansion

!!     previous command
!$     last argument
!^     first argument
!*     all arguments
!-n    n commands ago
!foo   last command: foo
!?foo  command containing"
        return 0
    elif [[ "$rem" == (#b)(![a-zA-Z0-9_-]##)(*) ]]; then
        ev_hint="Matches most recent command starting with '${match[1]#!}'"
        rem="${match[2]}"
        is_free_text=1
    else
        # Invalid event designator
        return 1
    fi
    
    # ---------------------------------------------------------
    # PART 2: Parse Modifiers and Word Designators loop
    # ---------------------------------------------------------
    local mod_hint=""
    while [[ -n "$rem" ]]; do
        # Exact match for trailing colon -> show multiline menu
        if [[ "$rem" == ":" ]]; then
            builtin print -r -- "Modifiers & Designators

:0-9   nth argument
:^ $ * first/last/all args
:p     print without running
:h :t  keep head / tail
:r :e  remove / keep ext
:s/x/y substitute x with y
:g     apply globally"
            return 0
        fi
        
        # Word designators that omit the colon (e.g., !!*)
        if [[ "$rem" != :* ]]; then
            if [[ "$rem" == (#b)([\$\*%\^])(*) ]]; then
                local m="${match[1]}"
                rem="${match[2]}"
                case "$m" in
                    \^) mod_hint="first argument selected" ;;
                    \$) mod_hint="last argument selected" ;;
                    \*) mod_hint="all arguments selected" ;;
                    %)  mod_hint="matched word selected" ;;
                esac
                continue
            else
                return 1
            fi
        fi
        
        # Now rem MUST start with a colon
        if [[ "$rem" == (#b)(:s|:gs)(*) ]]; then
            local mod="${match[1]}"
            local sub_rem="${match[2]}"
            
            # If nothing follows :s, wait for the delimiter
            if [[ -z "$sub_rem" ]]; then
                builtin print -r -- "Substitute
Next character sets your delimiter"
                return 0
            fi
            
            local delim="${sub_rem[1]}"
            local rest_sub="${sub_rem[2,-1]}"
            
            # Safely count unescaped delimiters
            local delim_count=0
            local cut_idx=0
            local i
            for (( i=1; i<=${#rest_sub}; i++ )); do
                if [[ "${rest_sub[i]}" == "$delim" ]]; then
                    # Check if the delimiter is escaped (e.g., \/)
                    if [[ $i -eq 1 || "${rest_sub[i-1]}" != '\' ]]; then
                        (( delim_count++ ))
                        if (( delim_count == 2 )); then
                            cut_idx=$i
                            break
                        fi
                    fi
                fi
            done
            
            # Evaluate substitute modifier state
            if (( delim_count == 0 )); then
                builtin print -r -- "Typing pattern to match
Ends at ${delim}"
                return 0
            elif (( delim_count == 1 )); then
                builtin print -r -- "Typing replacement
Ends at ${delim}"
                return 0
            elif (( delim_count == 2 )); then
                # Slice off the completed substitute block and continue parsing
                rem="${rest_sub[cut_idx+1,-1]}"
                mod_hint="substitution complete"
            else
                return 1
            fi
            
        elif [[ "$rem" == (#b)(:[0-9]##-[0-9]##|:[0-9]##\*|:[0-9]##-|:[0-9]##)(*) ]]; then
            local m="${match[1]}"
            rem="${match[2]}"
            mod_hint="word designator ${m#:} selected"
            
        elif [[ "$rem" == (#b)(:[\$\*%\^])(*) ]]; then
            local m="${match[1]}"
            rem="${match[2]}"
            case "$m" in
                :^) mod_hint="first argument selected" ;;
                :$) mod_hint="last argument selected" ;;
                :*) mod_hint="all arguments selected" ;;
                :%) mod_hint="matched word selected" ;;
            esac
            
        elif [[ "$rem" == (#b)(:[phtreqxc\&g])(*) ]]; then
            local m="${match[1]}"
            rem="${match[2]}"
            case "$m" in
                :p) mod_hint="print command without executing" ;;
                :h) mod_hint="keep head (remove tail)" ;;
                :t) mod_hint="keep tail (remove head)" ;;
                :r) mod_hint="remove extension" ;;
                :e) mod_hint="keep extension only" ;;
                ':&') mod_hint="repeat last substitution" ;;
                :g) mod_hint="apply next modifier globally" ;;
                :*) mod_hint="modifier ${m#:} applied" ;;
            esac
            
        else
            # Dead state (invalid modifier)
            return 1
        fi
    done
    
    # ---------------------------------------------------------
    # PART 3: Final Render (If we successfully consumed the whole string)
    # ---------------------------------------------------------
    if [[ -z "$rem" ]]; then
        local lines=()
        if [[ -n "$mod_hint" ]]; then
            lines=("$mod_hint" "" "[ : for more, Space/Enter to run ]")
        elif (( is_free_text )); then
            # Still typing !foo
            lines=("$ev_hint")
        else
            # Finished a closed-choice base event like !! or !-2
            lines=("$ev_hint" "" "[ : for modifiers, Space/Enter to use ]")
        fi
        
        builtin print -r -- "${(F)lines}"
        return 0
    fi
    return 1
}

# Thin interactive wrapper: resolve inner text, then add the box sugar.
_bang_hints_redraw_hook() {
    emulate -L zsh
    local msg
    if msg="$(_bang_hints_resolve "${LBUFFER:-}" "${RBUFFER:-}")"; then
        _bang_hints_show "$(_bang_hints_draw_box "${(@f)msg}")"
    else
        _bang_hints_clear
    fi
}

# Bind the hook globally (interactive shells only, so non-interactive
# `source` stays silent with status 0). add-zle-hook-widget dedupes,
# so re-sourcing is safe.
if [[ -o interactive ]]; then
    add-zle-hook-widget line-pre-redraw _bang_hints_redraw_hook 2>/dev/null || true
fi
: # keep source exit status 0 when the hook was skipped
