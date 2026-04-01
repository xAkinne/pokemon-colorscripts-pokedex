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
from rich.text import Text # rich text
from textual.app import App, ComposeResult # tui app
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer # layout
from textual.widgets import Input, ListItem, ListView, Static, Button # widgets
from textual.screen import Screen # screens
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
    return '\n'.join([l if l.strip() else l for l in plain.split('\n')]) # raw blocks

def make_bar(cur, tot, width=60): # custom bar
    if tot == 0: return "|" + "░" * width + "|" # empty
    done = int((cur / tot) * width) # filled part
    return "|" + "█" * done + "░" * (width - done) + "|" # bar string

# # TUI COMPONENTS
class PokeItem(ListItem): # list entry
    def __init__(self, idx, name, known): # init item
        super().__init__()
        self.p_idx, self.p_name, self.p_known = idx, name, known # store data
    def compose(self) -> ComposeResult: yield Static(f" {self.p_idx+1:04d}: {self.p_name if self.p_known else '???'}") # display

class DetailScr(Screen): # info screen
    BINDINGS = [
        ("escape", "back", "Back"),
        ("left", "prev", "Prev"),
        ("right", "next", "Next")
    ]
    def __init__(self, idx, pokes, db, map_data): # init details
        super().__init__()
        self.p_idx, self.p_pokes, self.p_db, self.p_map = idx, pokes, db, map_data # data
        self.update_data() # init state

    def update_data(self): # refresh state
        self.p_name = self.p_pokes[self.p_idx] # current name
        self.p_pid = self.p_idx + 1 # current id
        self.p_known = str(self.p_pid) in self.p_db["captured"] # check capture
        self.p_shiny = self.p_db["captured"].get(str(self.p_pid), {}).get("shiny", False) # check shiny

    def compose(self) -> ComposeResult: # build ui
        with ScrollableContainer(id="det-cont"): # scrollable
            yield Vertical(id="det-inner") # wrapper
        with Horizontal(id="det-nav"): # nav row
            yield Button("< Prev", id="btn-prev")
            yield Button("Bulbapedia", id="bulb-btn")
            yield Button("Next >", id="btn-next")
        with Horizontal(id="back-row"): # centered back row
            yield Button("Back (ESC)", id="back-btn")

    def on_mount(self): self.refresh_view() # first load

    def refresh_view(self): # update content
        cont = self.query_one("#det-inner", Vertical)
        for child in list(cont.children): child.remove() # manual clear
        
        if not self.p_known: # unknown
            v = Vertical(
                Static("Base Form", classes="form-lbl"),
                Static(shadow(get_sprite(self.p_name, True)), classes="sprite"),
                classes="sprite-col"
            )
            cont.mount(Horizontal(v, classes="sprite-row")) # Use class instead of ID
            cont.mount(Static(f"ID: {self.p_pid:04d}", classes="info-id"))
            cont.mount(Static("???", classes="name-big"))
        else: # discovered
            cols = [] # children list
            cols.append(Vertical(
                Static("Base Form", classes="form-lbl"),
                Static(Text.from_ansi(get_sprite(self.p_name, True)), classes="sprite"),
                classes="sprite-col"
            ))
            if self.p_shiny: # add shiny
                cols.append(Vertical(
                    Static("Shiny Form", classes="form-lbl"),
                    Static(Text.from_ansi(get_sprite(self.p_name, True, True)), classes="sprite"),
                    classes="sprite-col"
                ))
            
            cont.mount(Horizontal(*cols, classes="sprite-row")) # Use class instead of ID
            m_name = self.p_map.get(self.p_name, self.p_name.capitalize()) # name
            cont.mount(Static(f"ID: {self.p_pid:04d}", classes="info-id"))
            cont.mount(Static(m_name, classes="name-big"))

    def action_back(self): self.app.pop_screen() # close
    def action_prev(self): # go prev
        self.p_idx = (self.p_idx - 1) % len(self.p_pokes); self.update_data(); self.refresh_view()
    def action_next(self): # go next
        self.p_idx = (self.p_idx + 1) % len(self.p_pokes); self.update_data(); self.refresh_view()

    @on(Button.Pressed, "#back-btn")
    def on_back_click(self): self.action_back()
    @on(Button.Pressed, "#btn-prev")
    def on_prev_click(self): self.action_prev()
    @on(Button.Pressed, "#btn-next")
    def on_next_click(self): self.action_next()
    @on(Button.Pressed, "#bulb-btn")
    def open_link(self): # open web
        n = self.p_map.get(self.p_name, self.p_name.capitalize()).replace(" ", "_")
        webbrowser.open(f"https://bulbapedia.bulbagarden.net/wiki/{n}_(Pok%C3%A9mon)")

class Pokedex(App): # main app
    CSS = """
    Screen { background: #121212; align: center middle; }
    #main-wrap { width: 84; height: 100%; }
    #cont { padding: 1; width: 100%; height: 100%; background: #121212; }
    #header-lbl { text-align: center; width: 100%; text-style: bold; color: white; margin-bottom: 1; }
    #search { margin-bottom: 1; border: heavy white; width: 100%; background: #1e1e1e; color: white; }
    ListView { border: heavy white; width: 100%; height: 1fr; background: #1e1e1e; padding: 1 2; }
    ListItem { padding: 0 1; }
    ListItem:focus { background: #3a3a3a; text-style: bold; color: #ffffff; }
    .name-big { text-style: bold underline; margin-bottom: 1; width: 100%; text-align: center; color: white; height: 3; content-align: center middle; }
    .info-id { text-style: bold; width: 100%; text-align: center; color: white; margin-top: 1; }
    .form-lbl { text-align: center; width: 100%; text-style: bold; color: white; margin-bottom: 1; }
    .sprite { border: heavy white; padding: 1; width: auto; height: auto; background: #1e1e1e; align: center middle; }
    .sprite-row { height: auto; align: center middle; width: 100%; background: transparent; }
    .sprite-col { width: auto; align: center middle; height: auto; margin: 0 2; }
    #det-cont { height: 1fr; width: 100%; background: #121212; align: center middle; }
    #det-inner { align: center middle; width: 100%; height: auto; }
    #det-nav { height: 3; align: center middle; width: 100%; margin-top: 1; }
    #det-nav Button { margin: 0 1; border: heavy white; background: #1e1e1e; color: white; }
    #back-row { height: 3; align: center middle; width: 100%; margin-bottom: 2; margin-top: 2; }
    #back-btn { border: heavy white; background: #1e1e1e; color: white; width: 30; }
    #prog-cont { height: 6; width: 100%; margin-bottom: 1; align: center middle; }
    #prog-pct { text-align: center; width: 100%; color: white; text-style: bold; }
    #prog-bar { text-align: center; width: 100%; color: white; }
    #prog-cnt { text-align: center; width: 100%; color: white; }
    #foot-row { height: 3; width: 100%; align: center middle; }
    .foot-btn { margin: 0 1; border: heavy white; background: #1e1e1e; color: white; }
    """
    BINDINGS = [("/", "find", "Search"), ("s", "sort", "Sort"), ("q", "quit", "Quit")]
    def __init__(self): # init
        super().__init__()
        self.pokes, self.db, self.map = list_pokes(), get_db(), get_map()
        self.sort_mode = "id"
    def compose(self) -> ComposeResult: # build
        with Container(id="main-wrap"):
            with Vertical(id="cont"):
                yield Static("=== NATIONAL POKEDEX ===", id="header-lbl")
                with Vertical(id="prog-cont"): # 3-line progress
                    yield Static("", id="prog-pct") # line 1
                    yield Static("", id="prog-bar") # line 2
                    yield Static("", id="prog-cnt") # line 3
                yield Input(placeholder="Search ID/Name...", id="search")
                with ScrollableContainer(): yield ListView(id="list")
                with Horizontal(id="foot-row"):
                    yield Button("Search (/)", id="btn-find", classes="foot-btn")
                    yield Button("Sort (S)", id="btn-sort", classes="foot-btn")
                    yield Button("Quit (Q)", id="btn-quit", classes="foot-btn")
    def on_mount(self): self.update_list(); self.up_prog()
    def update_list(self, query=""): # filter
        lv = self.query_one("#list", ListView); lv.clear()
        items = []
        for i, n in enumerate(self.pokes):
            known = str(i+1) in self.db["captured"]
            if not query or query.isdigit() and query in str(i+1) or query.lower() in n.lower():
                items.append((i, n, known))
        if self.sort_mode == "known": items.sort(key=lambda x: (not x[2], x[0]))
        for i, n, known in items: lv.append(PokeItem(i, n, known))
    def up_prog(self): # stats
        got, tot = len(self.db["captured"]), len(self.pokes)
        pct = (got/tot*100) if tot > 0 else 0
        self.query_one("#prog-pct", Static).update(f"{pct:.1f}%")
        self.query_one("#prog-bar", Static).update(make_bar(got, tot, 60))
        self.query_one("#prog-cnt", Static).update(f"{got}/{tot}")
    @on(Input.Changed, "#search")
    def on_find(self, e): self.update_list(e.value)
    @on(ListView.Selected)
    def on_pick(self, e): self.push_screen(DetailScr(e.item.p_idx, self.pokes, self.db, self.map))
    @on(Button.Pressed, "#btn-find")
    def action_find(self): self.query_one("#search").focus()
    @on(Button.Pressed, "#btn-sort")
    def action_sort(self):
        self.sort_mode = "known" if self.sort_mode == "id" else "id"
        self.update_list(self.query_one("#search").value)
    @on(Button.Pressed, "#btn-quit")
    def action_quit(self): self.exit()

# # CLI
def catch_one(): # random
    c, db, p = get_conf(), get_db(), list_pokes()
    if not p: return
    n = random.choice(p); pid = str(p.index(n) + 1)
    is_s = random.randint(1, c.get("shiny_chance", 4096)) == 1
    print(get_sprite(n, False, is_s))
    if pid not in db["captured"]: db["captured"][pid] = {"normal": True, "shiny": False}
    else: db["captured"][pid]["normal"] = True
    if is_s: db["captured"][pid]["shiny"] = True
    put_db(db)

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        if len(sys.argv) > 1 and sys.argv[1] in ["-c", "--catch"]: catch_one()
        else: Pokedex().run()

@cli.command(name="catch")
def c_cmd(): catch_one()

@cli.command()
@click.argument('name')
@click.option('--shiny', is_flag=True)
def spawn(name, shiny):
    db, p = get_db(), list_pokes()
    if name not in p: return print(f"Unknown: {name}")
    pid = str(p.index(name) + 1)
    if pid not in db["captured"]: db["captured"][pid] = {"normal": True, "shiny": False}
    if shiny: db["captured"][pid]["shiny"] = True
    put_db(db); print(f"Caught {name} {'(shiny)' if shiny else ''}")

@cli.command()
def reset():
    c = get_conf(); p = c.get("confirm_phrase", "RESET MY POKEDEX")
    if input(f"Type '{p}' to confirm: ") == p:
        put_db({"captured": {}}); print("Wiped.")
    else: print("Abort.")

if __name__ == "__main__": cli()
