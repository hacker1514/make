#!/bin/bash

GREEN="\033[32m"
BLUE="\033[34m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
MAGENTA="\033[35m"
RESET="\033[0m"

echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${GREEN} Welcome To ${YELLOW}Make It Setup ${RESET}"
echo -e "${CYAN} Developer : ${MAGENTA}Niranjan Kumar K ${RESET}"
echo -e "${CYAN} Version   : ${RED}1.0 ${RESET}"
echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${YELLOW}Installing Make It...${RESET}"

mkdir -p "$HOME/.makeit" >/dev/null 2>&1

curl -L https://hacker1514.github.io/make/download/make_it_termux -o "$PREFIX/bin/makeit" >/dev/null 2>&1
chmod +x "$PREFIX/bin/makeit" >/dev/null 2>&1

echo ""
echo -e "${BLUE}----------------------------------------${RESET}"
echo -e "${GREEN} Make It Installed Successfully! ${RESET}"
echo -e "${BLUE}----------------------------------------${RESET}"
echo ""
echo -e "${YELLOW}Run: ${CYAN}makeit${RESET}"

rm -- "$0" >/dev/null 2>&1
