---
title: "Kast 2.0 Living Architecture Wiki — İçindekiler Haritası (MOC)"
type: map-of-content
status: active
date: 2026-09-22
domain: root
tags:
  - moc
  - index
  - architecture
  - wiki-root
---

# Kast 2.0 Living Architecture Wiki — İçindekiler Haritası (MOC)

Bu fihrist, Andrej Karpathy'nin **"LLM Wiki / Living Architecture"** paradigması uyarınca Kast 2.0 kod tabanının yaşayan, ilişkisel mimarisini ve atomik bilgi ağını haritalandırır.

Proje, sıralı kitap bölümleri yerine fonksiyonel mimari rollere ve Obsidian uyumlu wikilink (`\[\[sayfa-adi\]\]`) graf ağına göre modellenmiştir.

---

## 🏛️ Mimari Karar Kayıtları (ADRs)
*Projenin kritik tasarım tercihleri, alternatifleri ve ödünleşimleri (trade-offs).*

- [[adr-001-openxml-tab-based-parsing]] — Dublaj senaryolarında sekme (`\t`), tire ve künye ayrıştırmasının neden düz metin regex yerine OpenXML hiyerarşisiyle çözüldüğü.
- [[adr-002-strict-pdf-pagination-flow]] — Yaklaşık satır simülasyonu ve `dxpdf` kusurları sonrası Headless LibreOffice ve Word COM ile %100 kesin PDF akışına geçiş kararı.
- [[adr-003-native-table-grid-generation]] — Word ve OnlyOffice ile tam uyumlu `w:tcBorders` (Table Grid), satır bölünme koruması (`w:cantSplit`) ve dinamik font mirası.
- [[adr-004-hybrid-launcher-and-dual-ui]] — Argümansız çağrılarda görsel Textual TUI'yi, parametreli çağrılarda doğrudan CLI modunu başlatan hibrit mimari.
- [[adr-005-qt6-windows-studio-gui]] — Windows stüdyo ortamları için PySide6 tabanlı stüdyo temalı, sürükle-bırak destekli ve QThread iş parçacıklı masaüstü GUI mimarisi.
- [[adr-006-windows-standalone-installer-and-ci]] — Windows için PyInstaller klasör demeti, Inno Setup akıllı ofis tespiti (Word/LibreOffice sessiz kurulumu) ve GitHub Actions CI/CD yayın mimarisi.

---

## 🧱 Çekirdek Veri Şemaları (Core Models)
*Ayrıştırma, sayfalama ve tablo yazma aşamalarında taşınan atomik veri yapıları.*

- [[dialogue-line]] — Konuşmacı, replik metni, süre kodu ve kesin sayfa numarasını tutan atomik replik modeli.
- [[character-stats]] — Karakter bazında toplam replik adedi, ilk görünme sırası ve sayfa kümesini toplayan istatistik sınıfı.
- [[cast-extraction-result]] — Tablo yazıcıya ve arayüze iletilen tüm karakter istatistiklerini ve meta verileri barındıran toplu model.
- [[parsed-paragraph]] — Ayrıştırıcı ile paginator arasında taşınan ara paragraf veri yapısı.

---

## 🔍 Ayrıştırma ve Metin İşleme Motoru (Parsing Engine)
*Word OpenXML paragraflarını tarayan, künye ve zaman kodlarını temizleyen motor.*

- [[dubbing-docx-parser]] — DOCX dökümanındaki sekme ve tire yapısını analiz eden temel ayrıştırıcı motor.
- [[dubbing-pdf-parser]] — PDF dökümanlarından DOCX dönüşümü olmadan doğrudan diyalog ve sayfa ayrıştıran motor.
- [[metadata-filtering]] — `KNOWN_METADATA_KEYS` ve Türkçe büyük harf kuralı ile künye bilgilerini karaktere dönüşmekten koruyan filtre.
- [[timecode-detection]] — `TIMECODE_REGEX` deseniyle bağımsız süre kodlarını diyalog metinlerinden izole eden özellik.

---

## 📐 Sayfalama ve Mizanpaj Alt Sistemi (Pagination Subsystem)
*Repliklerin dökümandaki gerçek sayfa numaralarını %100 hassasiyetle tespit eden katman.*

- [[document-paginator]] — PDF, OpenXML kesmeleri ve mizanpaj simülatörünü yöneten çok katmanlı sayfa koordinatörü.
- [[pdf-matching-engine]] — `pdfplumber` ile normalize edilmiş metinler üzerinden repliklerin sayfasını bulan eşleme motoru.
- [[headless-pdf-converter]] — `soffice` ve Word COM ile arka planda sessizce geçici PDF üreten ve temizleyen dönüştürücü.
- [[pure-python-layout-paginator]] — Ofis yazılımı bulunmayan ortamlarda Pillow metrikleri ve 108pt asılı girintiyle çalışan mizanpaj simülatörü.

---

## 📄 Tablo Üretimi ve Tipografi (Document Generation)
*Analiz sonuçlarını Word içine pikselsel uyumla yazan bileşenler.*

- [[cast-table-writer]] — 4 sütunlu (Karakter, Replik Sayısı, Sayfalar, Notlar) kast tablosunu Word belgesine ekleyen sınıf.
- [[openxml-styling]] — `w:tcBorders`, `w:cantSplit` ve dikey ortalama XML etiketlerini enjekte eden stil motoru.
- [[document-font-detection]] — Senaryodaki baskın yazı tipini ve boyutunu istatistiksel frekans analiziyle bulan dinamik tipografi motoru.

---

## 💻 Kullanıcı Arayüzleri ve Dağıtım (Interfaces and Runtime)
*Kullanıcı etkileşimini, komut satırı bayraklarını ve platform kurulumunu üstlenen modüller.*

- [[hybrid-cli-dispatcher]] — `kast.py` komut satırı argümanları, bayraklar (`--count`, `--in-place`, `--pdf`, `--standalone`) ve orkestrasyon.
- [[terminal-user-interface]] — Textual tabanlı koyu temalı TUI, sürükle-bırak girdi temizliği, yerel dosya seçiciler ve canlı log.
- [[qt6-desktop-gui]] — PySide6 tabanlı stüdyo sınıfı masaüstü GUI, StudioTheme koyu paleti, DropZoneWidget ve ExtractionWorker mimarisi.
- [[pyinstaller-standalone-packaging]] — Bağımsız Windows PyInstaller paketleme (`kast.spec`), konsolsuz giriş noktası (`run_gui.py`) ve çoklu çözünürlüklü ikon üretici (`generate_icon.py`).
- [[inno-setup-installer]] — Inno Setup 6 kurulum sihirbazı (`installer.iss`), sistemde Word/LibreOffice arayan Pascal scriptleri ve sessiz LibreOffice kurulumu.
- [[github-actions-release-workflow]] — Windows ikili ve kurulum paketlerini derleyip GitHub Releases üzerinde yayımlayan tam otomatik CI/CD iş akışı (`release-windows.yml`).
- [[cross-platform-installers]] — Linux (`install.sh`), Windows (`install.ps1`, `install.bat`) ve kabuk başlatıcıları (`bin/kast`, `kast.cmd`).

---

## 📜 Günlük ve Yönetim
- [[log]] — Karpathy LLM Wiki kronolojik olay, değişiklik ve modelleme günlüğü.
