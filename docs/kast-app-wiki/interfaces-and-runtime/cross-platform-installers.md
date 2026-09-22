---
title: "Modül: Çapraz Platform Kurulum ve Dağıtım Betikleri"
type: module
domain: interfaces-and-runtime
tags:
  - installation
  - packaging
  - deployment
  - bash
  - powershell
---

# Modül: Çapraz Platform Kurulum ve Dağıtım Betikleri

Kast 2.0, kullanıcıların karmaşık Python veya sanal ortam konfigürasyonlarıyla uğraşmadan tek bir komutla sisteme entegre olabilmesi için tasarlanmış sağlam kurulum ve dağıtım betiklerine sahiptir.

İlgili mimari prensipler [[adr-004-hybrid-launcher-and-dual-ui]] ve [[adr-002-strict-pdf-pagination-flow]] kararlarıyla uyumludur.

## Kurulum Dosyaları ve Görevleri

| Dosya | Platform | Temel Görevi |
| :--- | :--- | :--- |
| `install.sh` | Linux / macOS (Bash) | Sanal ortam (`.venv`) kurar, LibreOffice paketini (apt/dnf/pacman/zypper) kontrol edip kurar, bağımlılıkları yükler ve `~/.local/bin/kast` sembolik bağını oluşturur. |
| `install.ps1` | Windows (PowerShell) | Python sanal ortamını kurar, LibreOffice kontrolü yapar (winget/choco desteği), bağımlılıkları yükler, `%USERPROFILE%\bin\kast.cmd` başlatıcısını oluşturur ve Kullanıcı `PATH` ortam değişkenine ekler. |
| `install.bat` | Windows (CMD) | Çift tıklamayla veya CMD'den `install.ps1` dosyasını `ExecutionPolicy Bypass` ile çalıştıran sarmalayıcı (wrapper). |
| `bin/kast` | Linux / macOS | Sanal ortamdaki Python'u ve ana betiği (`kast.py`) tetikleyen yürütülebilir kabuk başlatıcısı. |
| `kast.cmd` | Windows | Windows komut satırından sanal ortam Python'unu çağıran batch başlatıcısı. |
| `kast-gui.cmd` | Windows | Modern Qt6 Stüdyo GUI (`kast.py --gui`) arayüzünü doğrudan çağıran Windows batch başlatıcısı. |
| `uninstall.sh` / `uninstall.ps1` | Tüm Platformlar | Sembolik bağları ve başlatıcıları sistemden temizleyen kaldırma betikleri. |

## Otomatik LibreOffice Yönetimi

[[adr-002-strict-pdf-pagination-flow]] uyarınca sayfa tespitinde %100 doğruluk sağlamak için kurulum betikleri sistemde `soffice` bulunup bulunmadığını kontrol eder:
- **Linux:**
  - Fedora/RHEL: `sudo dnf install -y libreoffice-writer`
  - Ubuntu/Debian: `sudo apt-get install -y libreoffice-writer`
  - Arch Linux: `sudo pacman -S --noconfirm libreoffice-fresh`
  - openSUSE: `sudo zypper install -y libreoffice-writer`
- **Windows:**
  - Sistem PATH veya Program Files taranır; eksikse `winget install TheDocumentFoundation.LibreOffice` yönergesi verilir.

## Sudo / Root İzolasyonu

`install.sh`, güvenlik gereği `sudo` ile çalıştırılmayı engeller. Kurulum tamamen kullanıcının kendi ev dizininde (`$HOME/.local/bin` ve `$REPO_DIR/.venv`) gerçekleşir, böylece sistem Python paketleri bozulmaz.

## İlgili Sayfalar

- [[headless-pdf-converter]]
- [[hybrid-cli-dispatcher]]
- [[terminal-user-interface]]
- [[qt6-desktop-gui]]
- [[adr-002-strict-pdf-pagination-flow]]
- [[adr-005-qt6-windows-studio-gui]]
