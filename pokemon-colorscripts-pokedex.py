#!/usr/bin/env python3
import os # sys ops
import sys # args
import json # data
import random # rng
import subprocess # shell
import re # regex
import webbrowser # links
from pathlib import Path # paths

import click # cli
from rich.static import Static # rich ui
from rich.text import Text # text ui
from textual.app import App, ComposeResult # tui app
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer # layout
from textual.widgets import Header, Footer, Input, ListItem, ListView, Static as TextualStatic, Button, ProgressBar # widgets
from textual.screen import Screen # screens
from textual.binding import Binding # keys
from textual import on # events

# # PATHS & CONFIG
CONF_DIR = Path.home() / ".config" / "pokemon-colorscripts-pokedex" # config dir
DATA_DIR = Path.home() / ".local" / "share" / "pokemon-colorscripts-pokedex" # data dir
MAP_FILE = Path(__file__).parent / "mapping.json" # names map
CONF_FILE = CONF_DIR / "config.json" # user config
DB_FILE = DATA_DIR / "captured.json" # capture db

DEF_CONF = {"shiny_chance": 4096, "confirm_phrase": "RESET MY POKEDEX"} # default settings

# # DATA OPS
def setup(): # init dirs
    CONF_DIR.mkdir(parents=True, exist_ok=True) # make conf
    DATA_DIR.mkdir(parents=True, exist_ok=True) # make data
    if not CONF_FILE.exists(): # new config
        with open(CONF_FILE, 'w') as f: json.dump(DEF_CONF, f, indent=4)
    if not DB_FILE.exists(): # new db
        with open(DB_FILE, 'w') as f: json.dump({"captured": {}}, f, indent=4)

def get_conf(): setup(); return json.load(open(CONF_FILE)) # load conf
def get_db(): setup(); return json.load(open(DB_FILE)) # load db
def put_db(db): json.dump(db, open(DB_FILE, 'w'), indent=4) # save db
def get_map(): return json.load(open(MAP_FILE)) if MAP_FILE.exists() else {} # load map

# # UTILS
def list_pokes(): # get all names
    try: return [l.strip() for l in subprocess.check_output(["pokemon-colorscripts", "-l"], text=True).split('\n') if l.strip()]
    except: return [] # fail safe

def get_sprite(name, big=False, shiny=False): # fetch sprite
    cmd = ["pokemon-colorscripts", "-n", name, "--no-title"] # basic cmd
    if big: cmd.append("-b") # large
    if shiny: cmd.append("-s") # shiny
    try: return subprocess.check_output(cmd, text=True) # run
    except: return "" # error

def shadow(ansi): # make silhouette
    plain = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', ansi) # remove color
    return '\n'.join(["\033[0m" + l + "\033[0m" if l.strip() else l for l in plain.split('\n')]) # reset colors

# # TUI COMPONENTS
class PokeItem(ListItem): # list entry
    def __init__(self, pid, name, known): # init item
        super().__init__()
        self.pid, self.name, self.known = pid, name, known # store data
    def compose(self) -> ComposeResult: yield TextualStatic(f"{int(self.pid):04d}: {self.name if self.known else '???'}") # display

class DetailScr(Screen): # info screen
    BINDINGS = [("escape", "back", "Back")] # back key
    def __init__(self, pid, name, db, map_data): # init details
        super().__init__()
        self.pid, self.name, self.db, self.map = pid, name, db, map_data # data
        self.known = str(pid) in db["captured"] # check capture
        self.shiny = db["captured"].get(str(pid), {}).get("shiny", False) # check shiny
    def compose(self) -> ComposeResult: # build ui
        yield Header() # top
        with ScrollableContainer(id="det-cont"): # scrollable
            if not self.known: # unknown
                yield TextualStatic(shadow(get_sprite(self.name, True)), classes="sprite") # silhouette
                yield TextualStatic(f"ID: {int(self.pid):04d} | Name: ???", classes="info") # hidden info
                yield Button("Bulbapedia", disabled=True) # no link
            else: # discovered
                with Horizontal(classes="row"): # sprites
                    yield TextualStatic(get_sprite(self.name, True), classes="sprite") # normal
                    if self.shiny: yield TextualStatic(get_sprite(self.name, True, True), classes="sprite") # shiny
                m_name = self.map.get(self.name, self.name.capitalize()) # map name
                yield TextualStatic(f"ID: {int(self.pid):04d} | Name: {m_name}", classes="info") # info
                yield Button("Bulbapedia", id="bulb-btn", variant="primary") # link
        yield Footer() # bottom
    def action_back(self): self.app.pop_screen() # close
    @on(Button.Pressed, "#bulb-btn")
    def open_link(self): # open web
        n = self.map.get(self.name, self.name.capitalize()).replace(" ", "_") # format name
        webbrowser.open(f"https://bulbapedia.bulbagarden.net/wiki/{n}_(Pok%C3%A9mon)") # go

class Pokedex(App): # main app
    CSS = """
    #cont { padding: 1; } # main padding
    #search { margin-bottom: 1; } # input margin
    .info { font-weight: bold; margin: 1; } # text style
    .sprite { border: solid green; padding: 1; width: auto; height: auto; } # box
    .row { height: auto; align: center middle; } # alignment
    #det-cont { align: center middle; text-align: center; } # detail align
    #prog-cont { height: 3; margin-bottom: 1; } # bar size
    #prog-lbl { text-align: center; width: 100%; } # label align
    """
    BINDINGS = [("/", "find", "Search"), ("q", "quit", "Quit")] # hotkeys
    def __init__(self): # init app
        super().__init__()
        self.pokes, self.db, self.map = list_pokes(), get_db(), get_map() # load all
    def compose(self) -> ComposeResult: # main ui
        yield Header() # top
        with Container(id="cont"): # wrap
            with Vertical(id="prog-cont"): # progress
                yield TextualStatic("", id="prog-lbl") # text
                yield ProgressBar(total=len(self.pokes), id="bar") # visual
            yield Input(placeholder="Search ID/Name...", id="search") # search
            with ScrollableContainer(): yield ListView(id="list") # results
        yield Footer() # bottom
    def on_mount(self): self.refresh(); self.up_prog() # start ui
    def refresh(self, query=""): # filter list
        lv = self.query_one("#list", ListView); lv.clear() # clear current
        for i, n in enumerate(self.pokes): # scan all
            pid = i + 1; known = str(pid) in self.db["captured"] # state
            if not query or query.isdigit() and query in str(pid) or query.lower() in n.lower(): # filter
                lv.append(PokeItem(str(pid), n, known)) # add match
    def up_prog(self): # update bar
        got, tot = len(self.db["captured"]), len(self.pokes) # counts
        pct = (got/tot*100) if tot > 0 else 0 # percent
        self.query_one("#prog-lbl", TextualStatic).update(f"{got}/{tot} ({pct:.1f}%)") # label
        self.query_one("#bar", ProgressBar).progress = got # bar
    @on(Input.Changed, "#search")
    def on_find(self, e): self.refresh(e.value) # auto search
    @on(ListView.Selected)
    def on_pick(self, e): self.push_screen(DetailScr(e.item.pid, e.item.name, self.db, self.map)) # show details
    def action_find(self): self.query_one("#search").focus() # focus bar

# # CLI
def catch_one(): # random capture
    c, db, p = get_conf(), get_db(), list_pokes() # load data
    if not p: return # no list
    n = random.choice(p); pid = str(p.index(n) + 1) # pick one
    is_s = random.randint(1, c.get("shiny_chance", 4096)) == 1 # rng shiny
    print(get_sprite(n, False, is_s)) # show sprite
    if pid not in db["captured"]: db["captured"][pid] = {"normal": True, "shiny": False} # new catch
    if is_s: db["captured"][pid]["shiny"] = True # mark shiny
    put_db(db) # save

@click.group(invoke_without_command=True) # cli root
@click.pass_context
def cli(ctx): # entry point
    if ctx.invoked_subcommand is None: # no args
        if len(sys.argv) > 1 and sys.argv[1] in ["-c", "--catch"]: catch_one() # handle flag
        else: Pokedex().run() # run tui

@cli.command(name="catch") # catch cmd
def c_cmd(): catch_one() # run catch

@cli.command() # debug spawn
@click.argument('name') # poke name
@click.option('--shiny', is_flag=True) # shiny flag
def spawn(name, shiny): # add manual
    db, p = get_db(), list_pokes() # load
    if name not in p: return print(f"Unknown: {name}") # check
    pid = str(p.index(name) + 1) # get id
    if pid not in db["captured"]: db["captured"][pid] = {"normal": True, "shiny": False} # init
    if shiny: db["captured"][pid]["shiny"] = True # set shiny
    put_db(db); print(f"Caught {name} {'(shiny)' if shiny else ''}") # done

@cli.command() # clear data
def reset(): # wipe db
    c = get_conf(); p = c.get("confirm_phrase", "RESET MY POKEDEX") # get phrase
    if input(f"Type '{p}' to confirm: ") == p: # check
        put_db({"captured": {}}); print("Wiped.") # reset
    else: print("Abort.") # cancel

if __name__ == "__main__": cli() # run
