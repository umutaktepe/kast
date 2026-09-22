---
title: "ADR-004: Hibrit Başlatıcı ve Çift Modlu (TUI / CLI) Kullanıcı Arayüzü Mimarisi"
type: architecture-decision-record
status: accepted
date: 2026-09-14
domain: architecture-decisions
tags:
  - adr
  - interface
  - tui
  - cli
  - textual
  - launcher
---

# ADR-004: Hibrit Başlatıcı ve Çift Modlu (TUI / CLI) Kullanıcı Arayüzü Mimarisi

## Bağlam (Context)

Kast kullanıcı profili iki farklı gruptan oluşur:
1. **Teknik Olmayan Çevirmenler ve Yönetmenler:** Komut satırı bayraklarını, dosya yollarını yazmayı ve terminal parametrelerini karmaşık bulan, sürükle-bırak kolaylığı ve görsel form arayan kullanıcılar.
2. **Gelişmiş Kullanıcılar ve Otomasyon Betikleri:** Toplu işlem (batch processing), CI/CD akışları ve tek satırda dosya işleyip çıkmak isteyen hızlı komut satırı kullanıcıları.

Geleneksel olarak iki ayrı program (ör. `kast-gui` ve `kast-cli`) geliştirmek kod tekrarına, bakım zorluğuna ve kullanıcı kafa karışıklığına yol açar. Ayrıca tam teşekküllü masaüstü GUI araçları (PyQt, Electron vb.) yüzlerce megabaytlık bağımlılıklar getirmekte ve kurulumu zorlaştırmaktadır.

## Karar (Decision)

Tek bir giriş noktası (`bin/kast` $\rightarrow$ `kast.py`) üzerinden çalışan akıllı bir **Hibrit Başlatıcı** mimarisi benimsenmiştir:

1. **Argümansız Çağrıda TUI (`Textual`):** Kullanıcı terminalde sadece `kast` yazdığında Textual kütüphanesiyle inşa edilmiş koyu temalı, modern terminal kullanıcı arayüzü (`KastApp`) açılır.
2. **Argümanlı Çağrıda Doğrudan CLI:** Kullanıcı bir dosya yolu veya bayrak sağladığında (`kast senaryo.docx --count`), TUI katmanı hiç yüklenmeden doğrudan süper hızlı komut satırı boru hattı (`process_cast_document`) çalışır.
3. **Sürükle-Bırak Girdi Temizleme (`clean_drag_drop_path`):** Terminal pencerelerine dosya sürüklendiğinde işletim sisteminin veya terminal emülatörünün eklediği tırnak işaretleri (`"..."`, `'...'`), `file://` önekleri ve URL yüzde kodlamaları (`%20` vb.) otomatik temizlenir.
4. **Yerel İşletim Sistemi Dosya Seçici Köprüsü (`select_file_dialog`):**
   - *Windows:* Konsol kesintisi yaratmayan en hızlı yöntem olarak `tkinter.filedialog` (varsa), yedek olarak `CREATE_NO_WINDOW` bayraklı arka plan PowerShell komutu.
   - *Linux:* Sistemde bulunan `zenity`, `kdialog` veya `tkinter`.
   - *macOS:* AppleScript `osascript` köprüsü.
5. **Windows Konsol Uyumluluğu (`setup_windows_console`):** Windows terminalinde UTF-8 ve ANSI sanal terminal (VT) desteğini etkinleştirmek için Windows API (`kernel32.SetConsoleOutputCP(65001)`) çağrıları.

## Alternatifler (Alternatives Considered)

- **Alternatif 1: Ağır GUI Kütüphaneleri (PyQt / Tkinter / Electron):**
  - *Reddedilme Gerekçesi:* Ağır kurulum maliyeti, sistem kütüphanelerine sıkı bağımlılık ve headless sunucularda çalışamama. Textual TUI hem SSH üzerinde hem masaüstü terminalinde sıfır GUI bağımlılığıyla çalışır.
- **Alternatif 2: Sadece CLI (Arayüzsüz):**
  - *Reddedilme Gerekçesi:* Teknik olmayan çevirmenlerin terminal komutlarını ve dosya yollarını ezberlemesi pratikte mümkün değildir; arayüz eksikliği aracın stüdyo ortamında benimsenmesini engeller.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- Tek bir komut (`kast`) tüm kullanıcı profillerini kusursuz karşılar.
- Çapraz platformda (Linux, Windows, macOS) hafif ve estetik deneyim.
- Test edilebilirlik: TUI bileşenleri Textual'ın `run_test()` asenkron test mekanizmasıyla tam birim test kapsamına alınabilmiştir.

### Olumsuz / Kısıtlar:
- Çok eski Windows komut satırlarında (cmd.exe klasik konsol) ANSI VT işleme açık değilse renkler sınırlı olabilir; `setup_windows_console` bu kısıtı en aza indirir.

## İlgili Sayfalar

- [[terminal-user-interface]]
- [[hybrid-cli-dispatcher]]
- [[cross-platform-installers]]
- [[adr-002-strict-pdf-pagination-flow]]
