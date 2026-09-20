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

## Terminal tools

Three standalone Python tools are in `terminal-tools/` and need only Python's standard library:

- `./terminal-tools/wiki.py "query"` searches Wikipedia, then lets you read a result summary. Run without a query to be prompted.
- `./terminal-tools/rain.py` animates rain in the terminal. Press `q` or Ctrl+C to quit.
- `./terminal-tools/weather.py [city]` shows current conditions and a five-day forecast. Run `./terminal-tools/weather.py --set-city "City, Country"` once to save a default location.

Weather data comes from [Open-Meteo](https://open-meteo.com/); Wikipedia uses its public API.
