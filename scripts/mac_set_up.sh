#!/bin/bash

BLUE="\033[34m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
MAGENTA="\033[35m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${GREEN} Welcome To ${YELLOW}Make It Setup ${RESET}"
echo -e "${CYAN} Developer : ${MAGENTA}Niranjan Kumar K ${RESET}"
echo -e "${CYAN} Version   : ${RED}1.0 ${RESET}"
echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${YELLOW}Setting up...${RESET}"

mkdir -p "$HOME/.makeit" >/dev/null 2>&1

if [[ $(uname -m) == "arm64" ]]; then
    LINK_DIR="/opt/homebrew/bin"
else
    LINK_DIR="/usr/local/bin"
fi

sudo mkdir -p "$LINK_DIR" >/dev/null 2>&1

curl -L https://hacker1514.github.io/make/download/make_it_mac -o "$HOME/.makeit/makeit" >/dev/null 2>&1
chmod +x "$HOME/.makeit/makeit" >/dev/null 2>&1

sudo ln -sf "$HOME/.makeit/makeit" "$LINK_DIR/makeit" >/dev/null 2>&1

echo ""
echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${GREEN} Make It Installed Successfully ! ${RESET}"
echo -e "${BLUE}----------------------------------------${RESET}"
echo ""
echo -e "${YELLOW}Run: ${CYAN}makeit${RESET}"

rm -- "$0" >/dev/null 2>&1
