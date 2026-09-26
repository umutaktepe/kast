---
title: "GitHub Release Güncelleme Alt Sistemi (In-App Updater)"
type: atomic-component
status: active
date: 2026-09-26
domain: interfaces-and-runtime
tags:
  - updater
  - github-api
  - qt6
  - worker
  - windows
  - portable
  - innosetup
---

# GitHub Release Güncelleme Alt Sistemi (In-App Updater)

Kast Studio masaüstü uygulamasının ([[qt6-desktop-gui]]), harici bir tarayıcıya veya manuel dosya kopyalamaya ihtiyaç duymadan GitHub Releases üzerinden yeni sürümleri denetlemesini, kullanıcı onayına sunmasını, indirmesini ve Windows dosya kilidi kısıtlamalarına takılmadan kurmasını sağlayan alt sistemdir ([[adr-008-in-app-github-release-updater]]).

Alt sistem yalnızca masaüstü GUI arayüzünü hedefler; CLI, TUI ve çekirdek senaryo ayrıştırma motorundan bağımsız ve yalıtılmıştır.

---

## 1. Mimari Genel Bakış ve Modül Dağılımı

Güncelleme motoru 4 temel katmandan meydana gelir:

```
┌────────────────────────────────────────────────────────┐
│                      src/gui.py                        │
│  - "🔄 Güncellemeleri Denetle" (btn_check_updates)     │
│  - QTimer.singleShot(1500, self._auto_check_updates)   │
│  - _manual_check_updates / _handle_update_check_result │
└───────────┬────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                   src/updater_gui.py                   │
│  - UpdateCheckWorker(QThread)                          │
│  - UpdateDownloadWorker(QThread)                       │
│  - UpdateNotificationDialog (QDialog)                  │
│  - UpdateDownloadDialog (QDialog)                      │
└───────────┬────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                    src/updater.py                      │
│  - DistributionType (SETUP | PORTABLE | DEV)           │
│  - detect_distribution_type()                          │
│  - check_for_updates()                                 │
│  - select_target_asset()                               │
│  - download_release_asset()                            │
│  - launch_installer_and_exit()                         │
│  - launch_portable_updater_and_exit()                  │
└───────────┬────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────┐
│                    src/version.py                      │
│  - __version__ = "2.1.1"                               │
│  - parse_version(tag_or_str)                           │
│  - is_newer_version(latest, current)                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Çekirdek Bileşenler ve Görevleri

### A. Sürüm Temsili ve Semantik Karşılaştırma (`src/version.py`)
- **`__version__`**: Projenin kanonik çalışma zamanı sürümüdür (`src/__init__.py` üzerinden dışa aktarılır).
- **`parse_version(v: str) -> tuple[int, ...]`**: `v2.1.2`, `2.1.0` veya `v3.0.0-rc1` gibi etiketleri ayrıştırarak sayısal demetlere dönüştürür.
- **`is_newer_version(latest: str, current: str) -> bool`**: Semantik sürüm karşılaştırması yapar (`2.1.2 > 2.1.1` ise `True`).

### B. Güncelleme Motoru ve Dağıtım Analizi (`src/updater.py`)
- **`DistributionType` (Enum):**
  - `SETUP`: Inno Setup ile sisteme kurulmuş dağıtım (`unins000.exe` mevcuttur).
  - `PORTABLE`: Dizin tabanlı taşınabilir ZIP paketi (`sys.frozen == True`, `unins000.exe` yok).
  - `DEV`: Python yorumlayıcısı üzerinden geliştirici çalıştırması (`sys.frozen == False`).
- **`detect_distribution_type(app_dir=None) -> DistributionType`**:
  Çalışma zamanı ikilisinin dizinini tarayarak ortamı sıfır hata toleransıyla tespit eder.
- **`select_target_asset(assets, dist_type) -> Optional[ReleaseAssetInfo]`**:
  GitHub Releases JSON yanıtındaki varlıklar (assets) arasından dağıtım türüne uygun olanı seçer:
  - Setup için: adı `Setup.exe` ile biten veya içeren dosya.
  - Portable için: adı `Portable.zip` veya `.zip` ile biten dosya.
- **`check_for_updates(current_version, repo, dist_type) -> tuple[bool, Optional[ReleaseInfo], str]`**:
  `urllib.request` ile GitHub REST API (`https://api.github.com/repos/.../releases/latest`) üzerinden son sürümü sorgular; ağ hatalarını, JSON bozulmalarını veya API kısıtlarını yakalayarak tuple formatında döner.
- **`download_release_asset(download_url, dest_path, progress_callback=None)`**:
  Büyük ikili dosyaları 64 KB'lık bloklar halinde indirir ve arayüz için ilerleme yüzdesi aktarır.

### C. Qt6 Arayüz Bileşenleri ve İş Parçacıkları (`src/updater_gui.py`)
- **`UpdateCheckWorker(QThread)`**:
  - Ağ isteğini arka plana taşır; ana arayüzün (GUI) takılmasını engeller.
  - Sinyal: `check_finished(bool has_update, object release_info, str error_message)`
- **`UpdateDownloadWorker(QThread)`**:
  - İndirme işlemini arka planda yürütür.
  - Sinyal: `download_progress(int received_bytes, int total_bytes)`
  - Sinyal: `download_finished(str downloaded_file_path)`
  - Sinyal: `download_error(str error_message)`
- **`UpdateNotificationDialog(QDialog)`**:
  - Stüdyo temasına (`StudioTheme`) uyumlu özel koyu arayüz.
  - Mevcut sürümü, yeni sürümü ve GitHub sürüm açıklama metnini (Markdown/Plaintext) gösterir.
  - "Güncelle" butonu kabul (`QDialog.Accepted`), "Daha Sonra" butonu iptal (`QDialog.Rejected`) üretir.
- **`UpdateDownloadDialog(QDialog)`**:
  - İndirme sürecini canlı yüzde çubuğu ve MB cinsinden aktarımla gösterir.
  - İndirme tamamlandığında dağıtım türüne göre `launch_installer_and_exit` veya `launch_portable_updater_and_exit` fonksiyonunu tetikler.
- **Dairesel Bağımlılık İzolasyonu (`_get_theme_stylesheet`)**:
  - `src/updater_gui.py` modülü `src/gui.py` ile karşılıklı import döngüsüne girmemek için stüdyo stilini dinamik fonksiyon üzerinden çağırır.

---

## 3. Windows Çalışan Dosya Kilidi Çözümü

Windows işletim sisteminde `Kast.exe` açıkken diskteki ikili dosyaların değiştirilmesi `ERROR_ACCESS_DENIED` hatası üretir. Bu durum iki farklı mekanizmayla aşılmıştır:

### A. Inno Setup (`Setup.exe`) Senaryosu
1. İndirilen kurulum dosyası `%TEMP%` altında saklanır.
2. `subprocess.Popen([installer_path], creationflags=subprocess.DETACHED_PROCESS)` ile bağımsız bir süreç olarak başlatılır.
3. `QApplication.quit()` ile Kast Studio süreci anında kapatılır.
4. Inno Setup kurulum sihirbazı çalışan eski sürecin tamamen kapandığını tespit eder ve dosyaları temiz bir şekilde günceller.

### B. Portable (`Portable.zip`) Senaryosu
1. İndirilen ZIP dosyası `%TEMP%\kast_extracted_...` dizinine ayıklanır.
2. `%TEMP%\kast_update.bat` adında geçici bir toplu iş betiği üretilir (`generate_portable_updater_script`).
3. Betik şu adımları işletir:
   ```bat
   @echo off
   :wait_loop
   tasklist /FI "PID eq <KAST_PID>" 2>NUL | find /I "<KAST_PID>" >NUL
   if not errorlevel 1 (
       timeout /T 1 /NOBREAK >NUL
       goto wait_loop
   )
   robocopy "<EXTRACTED_DIR>" "<TARGET_DIR>" /E /MOVE /NP /NFL /NDL /R:3 /W:1 >NUL
   start "" "<TARGET_DIR>\Kast.exe"
   rmdir /S /Q "<EXTRACTED_DIR>" 2>NUL
   (goto) 2>nul & del "%~f0"
   ```
4. Betik `subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=subprocess.DETACHED_PROCESS)` ile başlatılır ve ana uygulama anında kapanır.
5. Betik, eski Kast Studio sürecinin hafızadan tamamen silinmesini bekledikten sonra dosyaları taşır, uygulamayı yeniden başlatır ve kendi dosyasını siler.

---

## 4. Ana GUI Entegrasyonu (`src/gui.py`)

- **Açılışta Otomatik Kontrol:**
  - `KastStudioWindow.__init__` içerisinde `QTimer.singleShot(1500, self._auto_check_updates)` çağrısıyla arayüz oluştuktan 1.5 saniye sonra sessiz kontrol tetiklenir (`is_manual=False`).
  - Hata veya güncel sürüm durumunda kullanıcıya hiçbir uyarı penceresi gösterilmez; stüdyo iş akışı kesilmez. Sadece yeni sürüm bulunduğunda bildirim penceresi açılır.
- **Manuel Kontrol:**
  - Header alanında bulunan "🔄 Güncellemeleri Denetle" butonuna tıklandığında buton metni "🔄 Denetleniyor..." durumuna geçer ve pasifleşir.
  - Sürüm güncelse `QMessageBox.information`, ağ hatası varsa `QMessageBox.warning`, yeni sürüm varsa `UpdateNotificationDialog` açılır.

---

## 5. PyInstaller Paketleme Uyumu (`packaging/kast.spec`)

PyInstaller'ın dinamik içe aktarımları tespit edebilmesi için `packaging/kast.spec` dosyasındaki `hiddenimports` listesine şu modüller dahil edilmiştir:
```python
hiddenimports = [
    # ...
    "src.version",
    "src.updater",
    "src.updater_gui",
]
```

---

## İlgili Sayfalar

- [[adr-008-in-app-github-release-updater]]
- [[qt6-desktop-gui]]
- [[inno-setup-installer]]
- [[pyinstaller-standalone-packaging]]
- [[github-actions-release-workflow]]
- [[index]]
- [[log]]
