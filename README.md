<p align="center">
  <img src="pokemon-colorscripts-pokedex.png" alt="Logo" width="200" height="200">
</p>

<h1 align="center">Pokemon Color Pokedex</h1>
<p align="center">Gotta Catch 'Em All in your Terminal!</p>

<br><br>

## Table of Contents
1. [Description](#description)
2. [Installation and Configuration](#installation-and-configuration)
3. [File Locations](#file-locations)
4. [Credits](#credits)
5. [License](#license)

## Description

**Pokemon Color Pokedex** is a dynamic TUI (Terminal User Interface) and CLI extension for the `pokemon-colorscripts` project. It adds a layer of progression to your terminal by tracking Pokémon that appear in your shell.

## Installation and Configuration

### Prerequisites
- [pokemon-colorscripts](https://gitlab.com/phoneybadger/pokemon-colorscripts) must be installed.
- Python 3.x

### System Installation (Recommended)
1. **Clone and Install:**
   ```bash
   git clone https://github.com/xAkinne/pokemon-colorscripts-pokedex.git
   cd pokemon-colorscripts-pokedex
   sudo ./install.sh
   ```
2. **Clean up:**
   You can safely delete the downloaded folder after installation.

### Manual Installation
1. **Install Dependencies:** `pip install textual click rich`
2. **Setup:** Copy `src/pokemon-colorscripts-pokedex.py` and `src/mapping.json` to a permanent folder and link the script to your `/usr/local/bin`.

## File Locations

To keep your system clean, the application uses the following paths:
- **Executable Logic:** `/opt/pokemon-colorscripts-pokedex/`
- **Global Command:** `/usr/local/bin/pokemon-colorscripts-pokedex`
- **Your Progress (Captured Pokémon):** `~/.local/share/pokemon-colorscripts-pokedex/captured.json`
- **Configuration (Shiny rates, etc.):** `~/.config/pokemon-colorscripts-pokedex/config.json`

## Credits

This project is a dedicated add-on for the amazing [pokemon-colorscripts](https://gitlab.com/phoneybadger/pokemon-colorscripts) by **phoneybadger**.

<hr>

<p align="center">
  <span>License: GNU GPL 3.0</span> | <span>Created by <a href="https://akinne.xyz">Akinne</a></span>
</p>
