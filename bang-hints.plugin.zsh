emulate -L zsh

_bang_hints_msg=$'! history expansion\n!!  previous command\n!$  last arg'

bang-hints-clear-and-insert() {
    emulate -L zsh
    zle -M ''
    zle -A .self-insert self-insert
    zle .self-insert -- "$KEYS"
}
zle -N bang-hints-clear-and-insert

bang-hints-show() {
    emulate -L zsh
    zle .self-insert -- "$KEYS"
    zle -M "$_bang_hints_msg"
    zle -N self-insert bang-hints-clear-and-insert
}
zle -N bang-hints-show

bindkey -M viins '!' bang-hints-show
