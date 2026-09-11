source "${ZDOTDIR}/../bang-hints.plugin.zsh"
bindkey -v
autoload -U colors && colors
# shellcheck disable=SC2034
PROMPT='%F{magenta}[DEV]%f %F{cyan}%~%f %# '
