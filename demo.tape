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
