# Airwave

Airwave is a native Qt internet radio and local music player for Hyprland,
Wayland, and other Linux desktops. It includes ambient, rock, pop, hip hop, and
lo-fi presets. Add station accepts HTTP(S) streams and playlists. Custom
stations and volume are saved in your desktop settings. Closing the window
stops playback and shuts down its private mpv process.

## Install and run the radio

Clone the repository and enter its directory:

```sh
git clone https://github.com/Fghau1/Airwave.git
cd Airwave
```

Install Python 3, `venv`, and mpv using your distribution's package manager.
For example:

```sh
# Arch Linux
sudo pacman -S python python-pip mpv

# Debian or Ubuntu
sudo apt install python3 python3-venv mpv

# Fedora
sudo dnf install python3 mpv
```

Create a virtual environment and install PySide6 into it:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip PySide6
```

Start Airwave from the repository folder (activate `.venv` first in a new
terminal):

```sh
python airwave.py
```

Choose a station to play. Use **Ctrl+O** to open a local audio file, **Ctrl+F**
to filter stations, and **Ctrl+Space** to pause or resume. Select **Add station**
to save another HTTP(S) radio stream. No Hyprland configuration changes are
required. Airwave talks to mpv through its
[JSON IPC](https://mpv.io/manual/stable/#json-ipc).

## Terminal apps

The standalone tools are in `terminal-tools/` and use only Python's standard
library. They do not need the Airwave virtual environment. Run them from the
repository folder:

```sh
# Search Wikipedia, then choose a result number to read its summary
./terminal-tools/wiki.py "Lisbon"

# Launch the animated terminal rain; press q or Ctrl+C to quit
./terminal-tools/rain.py

# Show current conditions and a five-day forecast for Lisbon
./terminal-tools/weather.py "Lisbon, Portugal"
```

Run `./terminal-tools/wiki.py` without a search term to be prompted. Run
`./terminal-tools/weather.py` without a city to use the saved default; on first
run it prompts for a city and remembers it. Set or change that default with:

```sh
./terminal-tools/weather.py --set-city "Lisbon, Portugal"
```

Wikipedia search and weather reports need an internet connection. Weather data
comes from [Open-Meteo](https://open-meteo.com/); the Wikipedia tool uses
Wikipedia's public API.
