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

İlgili mimari prensipler [[adr-004-hybrid-launcher-and-dual-ui]], [[adr-002-strict-pdf-pagination-flow]], [[adr-005-qt6-windows-studio-gui]] ve [[adr-006-windows-standalone-installer-and-ci]] kararlarıyla uyumludur.

## Kurulum Dosyaları ve Görevleri

| Dosya / Paket | Platform | Temel Görevi |
| :--- | :--- | :--- |
| `Kast-vX.Y.Z-Setup.exe` | Windows (x64) | **Resmi Bağımsız Kurulum Sihirbazı:** Python gerektirmez; Inno Setup 6 ile masaüstü/başlat kısayolları kurar, sistemde Word/LibreOffice denetimi yapar ve yoksa LibreOffice'i sessizce yükler ([[inno-setup-installer]]). |
| `Kast-vX.Y.Z-Windows-Portable.zip` | Windows (x64) | **Taşınabilir Bağımsız Sürüm:** Kurulum ve yönetici yetkisi gerektirmeyen, USB bellek veya yerel klasörden doğrudan çalışan PyInstaller klasör demeti ([[pyinstaller-standalone-packaging]]). |
| `install.sh` | Linux / macOS (Bash) | Sanal ortam (`.venv`) kurar, LibreOffice paketini kontrol edip kurar, bağımlılıkları (TUI, GUI ve motor) yükler ve `~/.local/bin/kast` sembolik bağını oluşturur (`kast`, `kast --gui`, `kast dosya.docx`). |
| `install.ps1` | Windows (PowerShell) | Geliştirici ve CLI kullanıcıları için sanal ortamı kurar, LibreOffice denetimi yapar, bağımlılıkları (TUI, GUI ve motor) yükler, `%USERPROFILE%\bin\kast.cmd` başlatıcısını oluşturur ve Kullanıcı `PATH` ortam değişkenine ekler (`kast`, `kast --gui`, `kast dosya.docx`). |
| `install.bat` | Windows (CMD) | Çift tıklamayla veya CMD'den `install.ps1` dosyasını `ExecutionPolicy Bypass` ile çalıştıran sarmalayıcı (wrapper). |
| `bin/kast` | Linux / macOS | Sanal ortamdaki Python'u ve ana betiği (`kast.py`) tetikleyen, tüm terminal parametrelerini (`$@`) ileten yürütülebilir kabuk başlatıcısı. |
| `kast.cmd` | Windows | Windows komut satırından sanal ortam Python'unu ve tüm parametreleri (`%*`) `kast.py` betiğine ileten tekil batch başlatıcısı. |
| `uninstall.sh` / `uninstall.ps1` | Tüm Platformlar | Sembolik bağları ve başlatıcıları sistemden temizleyen kaldırma betikleri. |

## Bağımsız Windows Paketleri (Zero-Python Dağıtım)

Kast 2.0, son kullanıcıların Python veya sanal ortam kurmasını gerektirmeyen bağımsız Windows dağıtımlarına sahiptir ([[adr-006-windows-standalone-installer-and-ci]]):
- **PyInstaller Demeti:** `packaging/kast.spec` ile tüm Qt6 ve ayrıştırma kütüphaneleri `dist/KastStudio/` içerisine derlenir.
- **Inno Setup Sihirbazı:** `packaging/installer.iss` ile derlenen kurulum dosyası, sistemde Word ve LibreOffice arar; ikisi de yoksa arka planda `winget` veya PowerShell ile LibreOffice'i otomatik ve sessiz kurar.
- **GitHub Actions CI/CD:** `.github/workflows/release-windows.yml` boru hattı ile her yeni sürümde kurulum dosyaları ve SHA256 özetleri otomatik üretilir ([[github-actions-release-workflow]]).

## Otomatik LibreOffice Yönetimi

[[adr-002-strict-pdf-pagination-flow]] uyarınca sayfa tespitinde %100 doğruluk sağlamak için kurulum betikleri sistemde `soffice` bulunup bulunmadığını kontrol eder:
- **Linux:**
  - Fedora/RHEL: `sudo dnf install -y libreoffice-writer`
  - Ubuntu/Debian: `sudo apt-get install -y libreoffice-writer`
  - Arch Linux: `sudo pacman -S --noconfirm libreoffice-fresh`
  - openSUSE: `sudo zypper install -y libreoffice-writer`
- **Windows (Geliştirici Scripti):**
  - Sistem PATH veya Program Files taranır; eksikse `winget install TheDocumentFoundation.LibreOffice` yönergesi verilir.
- **Windows (Kurulum Sihirbazı):**
  - Inno Setup Pascal scripti ile sistemde Word veya LibreOffice bulunmadığı takdirde kullanıcı müdahalesine gerek kalmadan sessizce kurulur.

## Sudo / Root İzolasyonu

`install.sh`, güvenlik gereği `sudo` ile çalıştırılmayı engeller. Kurulum tamamen kullanıcının kendi ev dizininde (`$HOME/.local/bin` ve `$REPO_DIR/.venv`) gerçekleşir, böylece sistem Python paketleri bozulmaz.

## İlgili Sayfalar

- [[inno-setup-installer]]
- [[pyinstaller-standalone-packaging]]
- [[github-actions-release-workflow]]
- [[adr-006-windows-standalone-installer-and-ci]]
- [[headless-pdf-converter]]
- [[hybrid-cli-dispatcher]]
- [[terminal-user-interface]]
- [[qt6-desktop-gui]]
- [[adr-002-strict-pdf-pagination-flow]]
- [[adr-005-qt6-windows-studio-gui]]
