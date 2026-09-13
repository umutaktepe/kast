#!/usr/bin/env bash
set -euo pipefail

# Renk tanımlamaları
GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
NC="\033[0m"

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  Kast 2.0 — Linux Kurulum ve Entegrasyon Scripti     ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Script dizinini tespit et
SOURCE_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
REPO_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"

# 1. Python 3 kontrolü
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}[Hata] Sistemde 'python3' bulunamadı.${NC}" >&2
    echo "Lütfen Python 3.10 veya daha yeni bir sürüm yükleyin." >&2
    exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo -e "${GREEN}✓${NC} Python $PY_VER bulundu."

# 2. Sanal ortam (.venv) kurulumu
VENV_DIR="$REPO_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}➜${NC} Sanal ortam (.venv) oluşturuluyor..."
    python3 -m venv "$VENV_DIR"
else
    echo -e "${GREEN}✓${NC} Mevcut sanal ortam (.venv) kullanılacak."
fi

# 3. Bağımlılıkların yüklenmesi
echo -e "${BLUE}➜${NC} Bağımlılıklar kontrol ediliyor..."
if "$VENV_DIR/bin/python3" -c "import docx, PIL, textual" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Gerekli tüm bağımlılıklar zaten sanal ortamda mevcut."
else
    echo -e "${BLUE}➜${NC} Eksik paketler yükleniyor (requirements.txt)..."
    if ! "$VENV_DIR/bin/pip" install --quiet -r "$REPO_DIR/requirements.txt"; then
        echo -e "${YELLOW}[Uyarı]${NC} pip ile paket yüklenirken internet bağlantısı hatası oluştu."
        echo -e "Lütfen internet bağlantınızı kontrol edip tekrar deneyin."
    else
        echo -e "${GREEN}✓${NC} Bağımlılıklar başarıyla yüklendi."
    fi
fi

# 4. Başlatıcı izinleri ve sembolik bağ oluşturma
LAUNCHER_SRC="$REPO_DIR/bin/kast"
chmod +x "$LAUNCHER_SRC"

LOCAL_BIN="${KAST_BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$LOCAL_BIN"

SYMLINK_TARGET="$LOCAL_BIN/kast"
ln -sf "$LAUNCHER_SRC" "$SYMLINK_TARGET"
echo -e "${GREEN}✓${NC} Başlatıcı bağlandı: $SYMLINK_TARGET -> $LAUNCHER_SRC"

# 5. PATH ortam değişkeni kontrolü
case ":$PATH:" in
    *":$LOCAL_BIN:"*)
        IN_PATH=1
        ;;
    *)
        IN_PATH=0
        ;;
esac

echo ""
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}  Kurulum Başarıyla Tamamlandı!                       ${NC}"
echo -e "${GREEN}======================================================${NC}"

if [ "$IN_PATH" -eq 1 ]; then
    echo -e "Artık herhangi bir terminal sekmesinden doğrudan:"
    echo -e "  ${YELLOW}kast${NC}              (Görsel TUI arayüzünü açar)"
    echo -e "  ${YELLOW}kast dosya.docx${NC}   (Hızlı komut satırı modunda çalıştırır)"
    echo -e "komutlarını kullanabilirsiniz."
else
    echo -e "${YELLOW}[Dikkat]${NC} '$LOCAL_BIN' dizini PATH ortam değişkeninizde bulunmuyor."
    echo -e "Komutu doğrudan kullanabilmek için kabuk konfigürasyonunuza (~/.bashrc veya ~/.zshrc) şunu ekleyin:"
    echo -e "  ${BLUE}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo -e "Geçici olarak aktif sekmede çalıştırmak için:"
    echo -e "  ${BLUE}export PATH=\"$LOCAL_BIN:\$PATH\"${NC}"
fi
echo ""
