---
title: "ADR-005: PySide6 (Qt6) Tabanlı Windows Stüdyo Masaüstü Grafik Arayüzü (GUI) Mimarisi"
type: architecture-decision-record
status: accepted
date: 2026-09-22
domain: architecture-decisions
tags:
  - adr
  - gui
  - pyside6
  - qt6
  - windows
  - studio
  - desktop
---

# ADR-005: PySide6 (Qt6) Tabanlı Windows Stüdyo Masaüstü Grafik Arayüzü (GUI) Mimarisi

## Bağlam (Context)

Kast senaryo ve dublaj kast tablosu çıkarma aracı, seslendirme ve dublaj stüdyolarında çalışan çevirmenler, kast direktörleri ve ses teknisyenleri tarafından yoğun olarak kullanılmaktadır. Bu kullanıcı grubunun belirgin operasyonel özellikleri şunlardır:

1. **Ağırlıklı Windows İşletim Sistemi Kullanımı:** Türkiye ve dünyadaki profesyonel dublaj ve ses kayıt stüdyolarının iş istasyonları (Pro Tools, Nuendo vb.) ağırlıklı olarak Windows ortamında çalışmaktadır.
2. **Terminal Yabancılığı ve Pratiklik Beklentisi:** Kullanıcıların büyük bölümü teknik yazılımcı olmayıp terminal komut satırını, parametre bayraklarını veya konsol pencerelerini karmaşık bulmakta; masaüstünde tek tıklamayla açılan, sürükle-bırak destekli görsel bir çalışma alanı talep etmektedir.
3. **Mevcut Arayüzlerin Yetersiz Kaldığı Noktalar:**
   - [[adr-004-hybrid-launcher-and-dual-ui]] ile hayata geçirilen Textual TUI arayüzü terminal meraklıları ve Linux/macOS kullanıcıları için son derece hafif ve etkili olsa da, Windows konsol emülatörlerinde (cmd.exe, eski conhost) ANSI renk işleme kısıtları, dosya sürüklemede kaçış karakteri problemleri ve pencerelerin terminal içinde hapsolması stüdyo akışını zorlaştırmaktadır.
   - Doğrudan dosya çıktı klasörünü açma ("Klasörde Göster"), oluşan Word dökümanını tek tıkla başlatma ("Dosyayı Aç"), format rozetleri (DOCX vs PDF) ve görsel ilerleme çubuğu gibi masaüstü entegrasyonları TUI ortamında kısıtlı kalmaktadır.
4. **Çok Formatlı Destek Gereksinimi:** Sistem hem Word (`.docx`) hem de doğrudan PDF (`.pdf`) senaryolarını kabul eder hale gelmiştir ([[dubbing-pdf-parser]]). Görsel arayüzün formatı anında tanıması, PDF seçildiğinde `in_place` seçeneğini kilitlemesi ve kullanıcıyı doğru aksiyonlara yönlendirmesi şarttır.

Bu gerekçelerle, Kast'ın stüdyolarda birincil araç olarak benimsenmesini sağlayacak tam teşekküllü, modern, koyu temalı bir yerel masaüstü arayüzüne (Desktop GUI) ihtiyaç duyulmuştur.

## Karar (Decision)

Kast 2.0 için **PySide6 (Qt 6.5+)** kütüphanesi temel alınarak stüdyo standartlarında bir masaüstü grafiksel kullanıcı arayüzü (`src/gui.py` ve `kast-gui.cmd`) geliştirilmiştir:

1. **Stüdyo Sınıfı Koyu Tema (`StudioTheme`):**
   - Tokyo Night ve modern DAW yazılımlarından ilham alan koyu palet (`#1a1b26` ana arka plan, `#24283b` kart arka planı, `#7aa2f7` birincil vurgu mavisi, `#9ece6a` başarı yeşili, `#f7768e` hata/PDF pembesi).
   - Windows ortamında net okuma sağlayan tipografi (`Segoe UI`, `Inter`) ve kapsamlı QSS stil sayfası (`get_stylesheet()`).
2. **Çift Durumlu Sürükle-Bırak Bileşeni (`DropZoneWidget`):**
   - Boş durumda geniş bırakma alanı, görsel ikon ve yerel dosya seçici butonu (`QFileDialog`).
   - Dosya yüklendiğinde format rozeti (DOCX için mavi, PDF için pembe), dosya adı, boyutu ve temizleme/değiştirme butonu.
   - Sürüklemede format doğrulaması (`.docx`, `.pdf`) ve görsel sınır vurgusu.
3. **Donmayan Arayüz ve Arka Plan İş Parçacığı (`ExtractionWorker` / `QThread`):**
   - Ağır PDF/Word ayrıştırma, sayfalama ve dosya kaydetme işlemleri GUI ana döngüsünden izole bir `QThread` üzerinde çalıştırılır.
   - İlerleme, konsol logları, tamamlanma ve hata durumları Qt Sinyalleri (`Signal`) aracılığıyla ana pencereye thread-safe olarak iletilir.
   - İşlem boyunca arayüz donmaz, ilerleme çubuğu ve konsol alanı dinamik olarak güncellenir.
4. **Birleşik Yönlendirici Entegrasyonu (`process_dubbing_file`):**
   - Worker içerisinden `kast.py`'daki `process_dubbing_file` API'si çağrılarak format ayrımı arka planda şeffaf biçimde yönetilir.
5. **Windows Başlatıcı ve Dağıtım:**
   - `%USERPROFILE%\bin\kast-gui.cmd` başlatıcısı ile Windows kullanıcılarının masaüstü veya Başlat menüsünden çift tıklayarak GUI'yi başlatabilmesi sağlanmıştır.
   - `install.ps1` kurulum betiği `PySide6` bağımlılığını ve GUI başlatıcısını otomatik kuracak şekilde genişletilmiştir.
   - CLI üzerinden `--gui` / `-g` bayrağı ile anında GUI çağrısı desteklenmiştir ([[hybrid-cli-dispatcher]]).

## Alternatifler (Alternatives Considered)

- **Alternatif 1: Tkinter / CustomTkinter:**
   - *Değerlendirme:* Python standart kütüphanesinde yer alması kurulum kolaylığı sağlar.
   - *Reddedilme Gerekçesi:* Standart Tkinter görsel olarak 1990'lar Windows görünümünde kalmıştır; modern koyu temaları ve tipografiyi desteklemez. CustomTkinter gibi topluluk sarmalayıcıları ise Windows DPI ölçeklendirmesinde bulanıklık yaratmakta, yerel dosya sürükle-bırak için kararsız üçüncü parti ikili tekerlekler (`tkinterdnd2`) gerektirmekte ve iş parçacığı güvenliği zayıf kalmaktadır.
- **Alternatif 2: Electron / Web Teknolojileri (HTML/CSS + Tauri veya PyInstaller):**
   - *Değerlendirme:* Web tabanlı modern arayüz ve CSS özelleştirmesi kolaydır.
   - *Reddedilme Gerekçesi:* Electron, Chromium motoru ve Node.js çalışma zamanı sebebiyle kurulum boyutunu 200MB+ artırmaktadır. Bellek tüketimi çok yüksektir. Python çekirdeği ile Node.js arasında karmaşık IPC köprüleri kurulmasını gerektirir ve başlatma gecikmesi stüdyo ortamı için kabul edilemez derecede yavaştır.
- **Alternatif 3: PyQt5 / PySide2 (Qt5):**
   - *Değerlendirme:* Yaygın kullanılan olgun Qt sarmalayıcılarıdır.
   - *Reddedilme Gerekçesi:* Qt5 serisinin resmi desteği (EOL) sona ermiştir. Modern 4K/HiDPI stüdyo monitörlerinde kesirli ölçekleme (fractional scaling) sorunları yaşanmaktadır. PySide6, Qt Company'nin resmi LGPLv3 kütüphanesi olup Python 3.10+ modern tip ipuçları ve Qt6'nın optimize edilmiş grafik mimarisini sunar.
- **Alternatif 4: Yalnızca TUI (Textual) ile Devam Etmek:**
   - *Değerlendirme:* Kurulumu hafif ve terminal içi kullanımı konforludur.
   - *Reddedilme Gerekçesi:* Windows stüdyo ortamlarında kullanıcıların terminal açma alışkanlığı bulunmamaktadır. İşletim sistemiyle tam entegre dosya sürükle-bırak, harici dosya yöneticisinde dökümanı açma ve modern pencereli arayüz beklentilerini karşılayamamaktadır.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- **Profesyonel Kullanıcı Deneyimi:** Çevirmenler ve ses teknisyenleri sıfır terminal komutuyla, tamamen görsel ve estetik bir stüdyo ortamında çalışabilir.
- **Duyarlı ve Kararlı Çalışma:** `QThread` tabanlı asenkron mimari sayesinde büyük senaryo dosyaları işlenirken dahi arayüz akıcı kalır ve donmaz.
- **Çift Format Uyumu:** Hem DOCX hem PDF dosyaları tek bir bırakma alanında otomatik tanınır ve uygun çıktı seçenekleri dinamik olarak aktifleşir.
- **Test Edilebilirlik:** `QT_QPA_PLATFORM=offscreen` ortam değişkeni sayesinde tüm GUI bileşenleri, sinyalleri ve iş parçacıkları headless sunucularda veya CI/CD boru hatlarında `pytest-qt` olmaksızın dahi saf `unittest/pytest` ile test edilebilmektedir.

### Olumsuz / Kısıtlar:
- **Bağımlılık Boyutu:** `PySide6`, sanal ortama (`.venv`) yaklaşık 50-60 MB ek boyut getirir. Ancak stüdyo iş istasyonları için bu boyut göz ardı edilebilir düzeydedir.
- **Ekran Sunucusu Gereksinimi:** Tamamen arayüzsüz (headless) Linux sunucularda GUI modu doğrudan başlatılamaz (`offscreen` bayrağı gerektirir); bu ortamlarda kullanıcılar doğrudan CLI veya TUI modunu kullanmalıdır.

## İlgili Sayfalar

- [[qt6-desktop-gui]]
- [[hybrid-cli-dispatcher]]
- [[cross-platform-installers]]
- [[dubbing-pdf-parser]]
- [[adr-004-hybrid-launcher-and-dual-ui]]
