---
title: "Modül: Inno Setup Windows Kurulum Sihirbazı ve Sessiz Ofis Denetimi"
type: module
status: active
date: 2026-09-23
domain: interfaces-and-runtime
tags:
  - packaging
  - innosetup
  - installer
  - windows
  - libreoffice
  - word
---

# Modül: Inno Setup Windows Kurulum Sihirbazı ve Sessiz Ofis Denetimi

Kast 2.0 Windows Studio Edition, `PyInstaller` ile derlenen bağımsız ikili klasörü (`dist/KastStudio/`) profesyonel bir yerel Windows kurulum sihirbazına (`Kast-vX.Y.Z-Setup.exe`) dönüştürmek için **Inno Setup 6** derleyicisini kullanır (`packaging/installer.iss`).

Bu kurulum sihirbazı; masaüstü ve başlat menüsü entegrasyonu, Türkçe/İngilizce çok dilli arayüz ve döküman sayfalama için hayati önem taşıyan Microsoft Word / LibreOffice varlığını denetleyen akıllı Pascal script mimarisi (`[Code]`) barındırır.

İlgili mimari kararlar ve bileşenler: [[pyinstaller-standalone-packaging]], [[github-actions-release-workflow]], [[headless-pdf-converter]], [[cross-platform-installers]] ve [[qt6-desktop-gui]].

---

## 1. Kurulum Mimarisi ve Dizin Yapısı

- **Hedef Dizin:** `{autopf}\{#MyAppName}` (`C:\Program Files\Kast Studio`)
- **64-Bit Mod:** `ArchitecturesInstallIn64BitMode=x64`
- **Sıkıştırma:** `Compression=lzma2/ultra64` ve `SolidCompression=yes`
- **Görsel Stil:** `WizardStyle=modern`
- **İkon ve Markalama:** `SetupIconFile=assets\kast.ico` ve `UninstallDisplayIcon={app}\assets\kast.ico`
- **Çok Dilli Destek (`[Languages]`):**
  - Türkçe (`compiler:Languages\Turkish.isl`) — Birincil / varsayılan
  - İngilizce (`compiler:Default.isl`)

---

## 2. Pascal Script (`[Code]`) ile Akıllı Ofis Tespiti

Kast 2.0 dublaj senaryosu sayfalama motoru ([[headless-pdf-converter]]), dökümanların kesin sayfa sınırlarını tespit etmek için yerel bir ofis motoruna (Microsoft Word veya LibreOffice) ihtiyaç duyar. Kurulum sihirbazı son kullanıcıya manuel bağımlılık yükleme yükü getirmemek adına sistem durumunu otomatik analiz eder:

### `IsWordInstalled(): Boolean`
1. `HKLM` ve `HKCU` altında `SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Winword.exe` anahtarını arar.
2. `HKCR` altında `Word.Application` COM nesne kaydını sorgular.

### `IsLibreOfficeInstalled(): Boolean`
1. `HKLM` ve `HKCU` altında `SOFTWARE\LibreOffice\UNO\InstallPath` anahtarını kontrol eder.
2. `HKLM` ve `HKCU` altında `SOFTWARE\The Document Foundation\LibreOffice` kayıtlarını denetler.
3. Yaygın kurulum yollarında `soffice.exe` varlığını tarar:
   - `{pf}\LibreOffice\program\soffice.exe` (64-bit Program Files)
   - `{pf32}\LibreOffice\program\soffice.exe` (32-bit Program Files)
   - `{localappdata}\Programs\LibreOffice\program\soffice.exe` (Kullanıcı bazlı kurulumlar)

---

## 3. Sessiz Arka Plan LibreOffice Kurulumu (`CurStepChanged`)

Sistemde Microsoft Word VEYA LibreOffice tespit edilirse kurulum ek hiçbir işlem yapmadan anında tamamlanır.

Eğer sistemde **İKİSİ DE YOKSA**, `ssPostInstall` adımında kullanıcıyı teknik ayrıntılarla rahatsız etmeden arka planda sessiz kurulum tetiklenir:

```pascal
if (not IsWordInstalled()) and (not IsLibreOfficeInstalled()) then
begin
  WizardForm.StatusLabel.Caption := 'Döküman sayfa doğrulaması için gerekli bileşenler hazırlanıyor (LibreOffice)...';
  // 1. Öncelik: winget sessiz kurulum
  // 2. Öncelik: PowerShell MSI indirme + msiexec /qn /norestart fallback
end;
```

1. **Öncelik 1 (`winget`):**
   `winget install --id TheDocumentFoundation.LibreOffice -e --silent --accept-package-agreements --accept-source-agreements` komutu gizli pencerede (`SW_HIDE`, `ewWaitUntilTerminated`) çalıştırılır.
2. **Öncelik 2 (PowerShell Fallback):**
   Eğer Windows paket yöneticisi (`winget`) mevcut değilse veya başarısız olursa; PowerShell arka planda resmi LibreOffice MSI paketini (`LibreOffice_latest_Win_x86-64.msi`) indirir ve `msiexec.exe /i ... /qn /norestart` ile sessizce kurar.

---

## 4. Kısayollar ve Kaldırma Entegrasyonu

- **Başlat Menüsü:** `{group}\{#MyAppName}` -> `{app}\{#MyAppExeName}`
- **Masaüstü:** `{autodesktop}\{#MyAppName}` -> `{app}\{#MyAppExeName}` (İsteğe bağlı `desktopicon` göreviyle)
- **Program Ekle/Kaldır:** `{uninstallexe}` başlatıcısı ve `kast.ico` stüdyo ikonu ile Windows Denetim Masası ve Ayarlar'a tescil edilir.
- **Son Ekran:** Kurulum bittiğinde kullanıcı `KastStudio.exe` uygulamasını doğrudan başlatabilir (`skipifsilent` ile sessiz kurulumlarda atlanır).

---

## 5. İlgili Sayfalar

- [[adr-006-windows-standalone-installer-and-ci]]
- [[pyinstaller-standalone-packaging]]
- [[github-actions-release-workflow]]
- [[headless-pdf-converter]]
- [[cross-platform-installers]]
- [[qt6-desktop-gui]]
