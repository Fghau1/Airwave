# Airwave

Native Qt radio and local music player for Hyprland / Wayland.

Run `python3 airwave.py` to start Airwave. Select a station to play. The app
includes ambient, rock, pop, hip hop, and lo-fi presets; Add station accepts
HTTP(S) streams and playlists. Custom stations and volume are saved through Qt
settings. Closing the window stops playback and shuts down its private mpv process.

- Ctrl+O: open a local audio file
- Ctrl+F: filter saved stations
- Ctrl+Space: pause / resume

Requires Python 3, PySide6, and mpv.
Source: `airwave.py`. No changes to Hyprland configuration are required.

Radio presets include SomaFM, ROCK ANTENNE, Hotmix Radio, and Back2HipHop.
Playback uses mpv JSON IPC: https://mpv.io/manual/stable/#json-ipc
