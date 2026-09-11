# bang-hints.plugin.zsh
#
# Provides interactive hints for Zsh history expansion (!).
# Driven by zle-line-pre-redraw to seamlessly handle typing, backspace, and pastes.

autoload -Uz add-zle-hook-widget

_bang_hints_redraw_hook() {
    # extendedglob is required for patterns like ## (1 or more occurrences)
    setopt localoptions extendedglob

    # 1. Isolate the current word being typed.
    # We strip everything up to the last whitespace or shell metacharacter.
    local current_word="${LBUFFER##*[ $'\t'|<>&;]}"

    # 2. Find the first '!' in the isolated word.
    local bang_idx=${current_word[(i)!]}

    # If no '!' is found, or it's escaped (\!), clear hint and abort.
    if ((bang_idx == 0 || bang_idx > ${#current_word})); then
        zle -M ''
        return
    fi

    # Check if the '!' is escaped (e.g., \!)
    local prefix=${current_word[1,bang_idx-1]}
    if [[ "$prefix" == *\\ ]]; then
        zle -M ''
        return
    fi

    # 3. Extract the bang string to run through the state machine.
    local bang_str=${current_word[bang_idx,-1]}
    local hint=""

    # 4. State Machine (v1 scope)
    case "$bang_str" in
    "!")
        hint="full menu: ! $ ^ * - ? word"
        ;;
    "!!")
        hint="!! → previous command"
        ;;
    "!"\$)
        hint="!$ → last argument of previous command"
        ;;
    "!^")
        hint="!^ → first argument of previous command"
        ;;
    "!*")
        hint="!* → all arguments of previous command"
        ;;
    "!-")
        # Pending closed-choice
        hint="type a digit → n commands ago"
        ;;
    "!"-[0-9]##)
        # Completed closed-choice
        hint="$bang_str → ${bang_str#!-} commands ago"
        ;;
    "!"\?)
        # Free-text start for containing word
        hint="matches most recent command containing this text — close with ?"
        ;;
    "!"\?*\?)
        # Self-closed terminator reached
        hint="search closed — : for a word designator, or space/enter to use"
        ;;
    "!"\?*)
        # Free-text span in progress
        hint="matches most recent command containing this text — close with ?"
        ;;
    "!"[a-zA-Z0-9_-]##)
        # Free-text matching word start
        hint="matches most recent command starting with '${bang_str#!}'"
        ;;
    *)
        # Dead state: Invalid character typed, or span implicitly ended
        hint=""
        ;;
    esac

    # 5. Render (ANSI codes removed to prevent ^[[ clutter)
    if [[ -n "$hint" ]]; then
        zle -M "$hint"
    else
        zle -M ''
    fi
}

# Bind the hook globally
add-zle-hook-widget line-pre-redraw _bang_hints_redraw_hook
