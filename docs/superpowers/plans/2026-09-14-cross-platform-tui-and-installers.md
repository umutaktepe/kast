# Cross-Platform TUI ve Linux/Windows Başlatıcıları Uygulama Planı

Kast 2.0 dublaj kast çıkarma programına hem Linux hem de Windows terminallerinde tek komutla (`kast`) açılan, görsel Textual TUI arayüzü ve her iki işletim sistemi için otomatik kurulum scriptleri (`install.sh` / `install.ps1`) eklenmesi.

## User Review Required

> [!IMPORTANT]
> - **Akıllı Hibrit Başlatma:** Terminalde sadece `kast` yazıldığında tam ekran Textual TUI açılır. Ancak argüman verildiğinde (`kast film.docx --count`) doğrudan hızlı CLI modunda çalışır.
> - **Otomatik Kurulum Scriptleri:** Linux için `install.sh` (`~/.local/bin/kast` sembolik bağı ile), Windows için `install.ps1` (`%USERPROFILE%\bin\kast.cmd` ve Kullanıcı PATH eklemesi ile) geliştirilecektir.
> - **TUI Kütüphanesi:** Modern, koyu temalı ve zengin bileşenli `textual` kütüphanesi kullanılacaktır.

## Proposed Changes

### 1. Bağımlılıklar ve Temel Altyapı

#### [MODIFY] [requirements.txt](file:///home/umutaktepe/Kast/requirements.txt)
- `textual>=0.80.0` eklenmesi.

---

### 2. TUI Uygulaması

#### [NEW] [src/tui.py](file:///home/umutaktepe/Kast/src/tui.py)
- `KastApp(App)` sınıfı:
  - **Başlık Çubuğu:** "Kast 2.0 — Dublaj Çevirisi Kast Çıkarma"
  - **Girdi Alanı (DOCX):** Sürükle-bırak destekli metin kutusu (tırnak işaretlerini otomatik temizler).
  - **Opsiyonel Girdi Alanı (PDF):** Referans PDF dosyası için sürükle-bırak kutusu.
  - **Sıralama Seçenekleri (RadioSet):**
    - `İlk Görünme Sırası (Appearance)` (Varsayılan)
    - `Replik Sayısına Göre (Count)`
    - `Karakter Adına Göre (A-Z)`
  - **Çıktı Seçenekleri (Checkbox):**
    - `Orijinal dosyanın sonuna ekle (--in-place)`
    - `Sadece kast tablosunu ayrı DOCX olarak kaydet (--standalone)`
    - Karşılıklı dışlama (biri seçildiğinde diğeri otomatik kapanır).
  - **İşlem Butonları:**
    - `[Kast Tablosunu Çıkar]` (Yeşil vurgulu buton)
    - `[Temizle]`
    - `[Çıkış (Q)]`
  - **Canlı Durum ve Sonuç Özeti Paneli:**
    - Toplam paragraf sayısı, tespit edilen replik sayısı, karakter sayısı ve üretilen dosya yolu.
- `launch_tui() -> int` fonksiyonu.

---

### 3. CLI ve Hibrit Başlatıcı

#### [MODIFY] [kast.py](file:///home/umutaktepe/Kast/kast.py)
- Argümansız çalıştırıldığında (`len(sys.argv) == 1`) otomatik olarak `launch_tui()` çağrısı yapılması.
- `--tui` ve `--cli` bayrakları ile modun zorlanabilmesi.
- Dosya yolu veya flag verildiğinde mevcut CLI modunda kesintisiz çalışmaya devam edilmesi.

---

### 4. Linux Başlatıcı ve Kurulum Scripti

#### [NEW] [bin/kast](file:///home/umutaktepe/Kast/bin/kast)
- `.venv/bin/python3` yolunu otomatik tespit eden ve `kast.py "$@"` çalıştıran yürütülebilir bash wrapper scripti.

#### [NEW] [install.sh](file:///home/umutaktepe/Kast/install.sh)
- Linux için tek tıkla/komutla kurulum:
  1. Python 3 kontrolü.
  2. `.venv` sanal ortamının oluşturulması/güncellenmesi ve `pip install -r requirements.txt`.
  3. `~/.local/bin` dizinine `kast` sembolik bağının oluşturulması (`chmod +x`).
  4. PATH kontrolü ve bilgilendirme.

---

### 5. Windows Başlatıcı ve Kurulum Scripti

#### [NEW] [kast.cmd](file:///home/umutaktepe/Kast/kast.cmd)
- Windows terminalinde `.venv\Scripts\python.exe kast.py %*` çağıran batch dosyası.

#### [NEW] [install.ps1](file:///home/umutaktepe/Kast/install.ps1)
- Windows PowerShell otomatik kurulum:
  1. Python kontrolü.
  2. `.venv` oluşturma ve `requirements.txt` yükleme.
  3. `%USERPROFILE%\bin` dizinine `kast.cmd` ekleme.
  4. Kullanıcı `PATH` ortam değişkenine `%USERPROFILE%\bin` dizinini otomatik ekleme.

---

### 6. Testler

#### [NEW] [tests/test_tui.py](file:///home/umutaktepe/Kast/tests/test_tui.py)
- Textual'ın `app.run_test()` altyapısı ile TUI widget yükleme, buton tıklama ve kast çıkarma testleri.

#### [MODIFY] [tests/test_integration.py](file:///home/umutaktepe/Kast/tests/test_integration.py)
- Argümansız başlatıldığında TUI tetikleme testi.

---

### 7. Dokümantasyon

#### [MODIFY] [README.md](file:///home/umutaktepe/Kast/README.md)
- TUI kullanım kılavuzu, ekran yerleşimi, Linux (`./install.sh`) ve Windows (`install.ps1`) kurulum yönergeleri.

---

## Verification Plan

### Automated Tests
- `pytest` ile tüm testlerin (mevcut 55 + yeni TUI testleri) çalıştırılması:
  ```bash
  .venv/bin/pytest -v
  ```
- Textual headless testlerinin doğrulanması:
  ```bash
  .venv/bin/pytest tests/test_tui.py -v
  ```

### Manual Verification
- Linux terminalinde `bin/kast` çalıştırılarak TUI ekranının açıldığının, koyu temanın ve butonların doğru render edildiğinin doğrulanması.
- CLI geriye dönük uyumluluk testi:
  ```bash
  bin/kast --help
  bin/kast --count
  ```
- Kurulum scriptinin (`./install.sh`) çalıştırılarak `~/.local/bin/kast` linkinin oluşturulduğunun ve terminalde doğrudan `kast` yazılabildiğinin doğrulanması.
