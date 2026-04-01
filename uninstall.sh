#!/bin/bash
# # UNINSTALLER: pokemon-colorscripts-pokedex

# # COLORS
RED='\033[0;31m'
NC='\033[0m'

# # REQUIRE SUDO
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo).${NC}"
    exit 1
fi

REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo -e "${RED}Uninstalling system-wide...${NC}"

# # REMOVE FILES
rm -rf "/opt/pokemon-colorscripts-pokedex"
rm -f "/usr/local/bin/pokemon-colorscripts-pokedex"

# # CLEANUP SHELL CONFIG
clean_rc() {
    local rc_file=$1
    if [ -f "$rc_file" ]; then
        sed -i '/# # pokemon-colorscripts-pokedex catch/d' "$rc_file"
        sed -i '/pokemon-colorscripts-pokedex catch/d' "$rc_file"
        sed -i "/alias pokedex='pokemon-colorscripts-pokedex'/d" "$rc_file"
        echo "Cleaned up $rc_file"
    fi
}

clean_rc "$REAL_HOME/.bashrc"
clean_rc "$REAL_HOME/.zshrc"

echo -e "${RED}Uninstalled successfully.${NC}"
