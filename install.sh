#!/bin/bash
# # INSTALLER: pokemon-colorscripts-pokedex (System-wide)

# # COLORS
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# # REQUIRE SUDO
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo).${NC}"
    exit 1
fi

# # GET ACTUAL USER (not root)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo -e "${GREEN}Starting system-wide installation...${NC}"

# # CHECK PYTHON
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required.${NC}"
    exit 1
fi

# # INSTALL DIR
INSTALL_DIR="/opt/pokemon-colorscripts-pokedex"
mkdir -p "$INSTALL_DIR"

# # COPY FILES
cp src/pokemon-colorscripts-pokedex.py "$INSTALL_DIR/"
cp src/mapping.json "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/pokemon-colorscripts-pokedex.py"

# # GLOBAL BINARY
ln -sf "$INSTALL_DIR/pokemon-colorscripts-pokedex.py" "/usr/local/bin/pokemon-colorscripts-pokedex"

# # INSTALL DEPS
echo -e "Installing Python dependencies..."
python3 -m pip install textual click rich --break-system-packages 2>/dev/null || python3 -m pip install textual click rich

# # SHELL CONFIG
SHELL_CONF=""
# Detect shell for the real user
USER_SHELL=$(getent passwd "$REAL_USER" | cut -d: -f7)
case "$USER_SHELL" in
    */zsh) SHELL_CONF="$REAL_HOME/.zshrc" ;;
    */bash) SHELL_CONF="$REAL_HOME/.bashrc" ;;
esac

if [ -n "$SHELL_CONF" ]; then
    # # ADD CATCH
    echo -n "Add automatic 'catch' to $SHELL_CONF? (y/n): "
    read REPLY
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i '1i# # pokemon-colorscripts-pokedex catch\npokemon-colorscripts-pokedex catch' "$SHELL_CONF"
        echo -e "${GREEN}Catch command added to $SHELL_CONF${NC}"
    fi

    # # ADD ALIAS
    echo -n "Create 'pokedex' alias? (y/n): "
    read REPLY
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "alias pokedex='pokemon-colorscripts-pokedex'" >> "$SHELL_CONF"
        chown "$REAL_USER:$REAL_USER" "$SHELL_CONF"
        echo -e "${GREEN}Alias created in $SHELL_CONF${NC}"
    fi
fi

# # FIX OWNERSHIP
chown -R "$REAL_USER:$REAL_USER" "$INSTALL_DIR"

echo -e "${GREEN}Installation complete! You can now delete the source folder.${NC}"
echo -e "Command: ${GREEN}pokemon-colorscripts-pokedex${NC} (or 'pokedex' if aliased)"
