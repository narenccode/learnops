S="C:/Users/nagas/AppData/Local/Temp/claude/a173b1655201fa07/6f3fc4fd-484a-4801-92de-d765aeb8d686/scratchpad"
python build_deck.py "$S/tpl.pptx" LearnOps_Interim_Presentation_Final.pptx || exit 1
W=$(cygpath -w "$PWD"); rm -rf png
powershell -NoProfile -File render.ps1 "$W\LearnOps_Interim_Presentation_Final.pptx" "$W\png" 2>&1 | head -3
