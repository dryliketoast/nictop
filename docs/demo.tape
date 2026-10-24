# Renders docs/demo.gif.  Run from the repo root:  vhs docs/demo.tape
# Assumes `nictop` is on PATH, some interface traffic is flowing, and a
# throwaway HOME so your own ~/.config/nictop/config.json is left alone.
Output docs/demo.gif
Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 600
Set Padding 12
Set TypingSpeed 60ms

Type "nictop --theme dracula" Enter
Sleep 9s
Type "b" Sleep 3s
Type "b" Sleep 2s
Type "t" Sleep 1500ms
Type "t" Sleep 1500ms
Type "t" Sleep 1500ms
Type "t" Sleep 3s
Type "q" Sleep 1s
