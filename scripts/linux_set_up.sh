#!/bin/bash

BLUE="\033[34m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
MAGENTA="\033[35m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${GREEN} Welcome To ${YELLOW}Make It Setup${RESET}"
echo -e "${CYAN} Developer : ${MAGENTA}Niranjan Kumar K${RESET}"
echo -e "${CYAN} Version   : ${RED}1.0${RESET}"
echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${YELLOW}Setting up...${RESET}"

mkdir -p "$HOME/.makeit"

curl -fsSL https://hacker1514.github.io/make/download/make_it_linux -o "$HOME/.makeit/makeit" || {
    echo -e "${RED}Download failed.${RESET}"
    exit 1
}

chmod +x "$HOME/.makeit/makeit"

if [ -w /usr/local/bin ]; then
    ln -sf "$HOME/.makeit/makeit" /usr/local/bin/makeit
else
    sudo ln -sf "$HOME/.makeit/makeit" /usr/local/bin/makeit
fi

echo
echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${GREEN}Make It Installed Successfully!${RESET}"
echo -e "${BLUE}----------------------------------------${RESET}"
echo
echo -e "${YELLOW}Run: ${CYAN}makeit${RESET}"

rm -- "$0" 2>/dev/null
