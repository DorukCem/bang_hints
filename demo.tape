Output demo.gif
Require zsh

Set Shell zsh
Set FontSize 20
Set Width 1100
Set Height 650
Set TypingSpeed 100ms

# Setup (hidden): load the plugin, use a minimal prompt, start clean.
Hide
Type "source ./bang-hints.plugin.zsh"
Enter
Sleep 1s
Type "PROMPT='%# '"
Enter
Sleep 500ms
Type "bindkey ' ' magic-space"
Enter
Sleep 500ms
Type "unsetopt HIST_VERIFY"
Enter
Sleep 500ms
Type "history -c"
Enter
Sleep 500ms
Type "clear"
Enter
Sleep 500ms
Show
Sleep 500ms

# 1. Bare ! -> base menu
Type "!"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 2. !! -> previous command
Type "!!"
Sleep 1.5s

# 3. !!: -> modifiers menu
Type ":"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 4. !$ -> last argument
Type "!$"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 5. !^ -> first argument
Type "!^"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 6. !* -> all arguments
Type "!*"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 7. !vim -> prefix search
Type "!vim"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 8. !?vim? -> closed search
Type "!?vim?"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 9. !-2 -> n commands ago
Type "!-2"
Sleep 1.5s

# 10. :p dry-run modifier
Type ":p"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 11. substitution
Type "!!:s/vim/nvim/"
Sleep 1.5s
Ctrl+U
Sleep 500ms

# 12. real-world idiom
Type "sudo !!"
Sleep 2s
Ctrl+U
Sleep 500ms

# 13. live typo-fix: truncated filename, substitution, expansion operator
Type "touch temp_file"
Sleep 500ms
Enter
Sleep 1s
Type "mv ./temp_f /tmp/"
Sleep 500ms
Enter
Sleep 1s
Type "!!"
Sleep 1.5s
Type ":"
Sleep 1.5s
Type "s"
Sleep 1s
Type "/"
Sleep 1s
Type@250ms "temp_f"
Sleep 1s
Type "/"
Sleep 1s
Type@250ms "temp_file"
Sleep 1s
Type "/"
Sleep 1.5s
Space
Sleep 1s
Enter
Sleep 1.5s
