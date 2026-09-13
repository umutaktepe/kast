#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
NC="\033[0m"

# Sudo kontrolü
if [ -n "${SUDO_USER:-}" ] && [ "${EUID:-$(id -u)}" -eq 0 ]; then
    echo -e "${RED}[Hata] Bu script 'sudo' ile çalıştırılmamalıdır!${NC}" >&2
    echo -e "Lütfen normal kullanıcınızla çalıştırın: ./uninstall.sh" >&2
    exit 1
fi

LOCAL_BIN="${KAST_BIN_DIR:-$HOME/.local/bin}"
TARGET="$LOCAL_BIN/kast"

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  Kast 2.0 — Linux Kaldırma (Uninstall) Scripti       ${NC}"
echo -e "${BLUE}======================================================${NC}"

if [ -L "$TARGET" ] || [ -f "$TARGET" ]; then
    rm -f "$TARGET"
    echo -e "${GREEN}✓${NC} Terminal başlatıcısı ($TARGET) başarıyla kaldırıldı."
else
    echo -e "${YELLOW}ℹ${NC} Başlatıcı ($TARGET) bulunamadı veya zaten silinmiş."
fi

REPO_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

echo ""
echo -e "${GREEN}Kast 2.0 terminal entegrasyonu başarıyla kaldırıldı.${NC}"
echo -e "Eğer proje dosyalarını ve sanal ortamı (.venv) da tamamen silmek isterseniz:"
echo -e "  ${YELLOW}rm -rf \"$REPO_DIR\"${NC}"
echo ""
