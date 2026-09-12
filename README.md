# bang-hints

Hints for zsh history expansion (`!`). Never executes, only shows.

Requires: zsh >= 5.0, UTF-8 locale, `setopt BANG_HIST` (default on).

## Install

Manual:

```zsh
git clone https://github.com/DorukCem/bang_hints ~/bang_hints
# add the following line to your ~/.zshrc
source ~/bang_hints/bang-hints.plugin.zsh
```

Oh-my-zsh:

```zsh
git clone https://github.com/DorukCem/bang_hints ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/bang-hints
# Add the plugin to the list of plugins inside ~/.zshrc
plugins=(
    # other plugins...
    bang-hints
)
```

## Usage

As you type history expansion expressions with the `!` operator you
will see hints on how you can use history expansion and its modifiers.

## Uninstallation

1. Remove the code referencing this plugin from ~/.zshrc
2. Remove the git repository from your hard drive

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
See the [LICENSE](LICENSE) file for details.
