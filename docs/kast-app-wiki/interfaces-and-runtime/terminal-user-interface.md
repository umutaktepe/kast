---
title: "Modül: Terminal Kullanıcı Arayüzü (Terminal User Interface - TUI)"
type: module
domain: interfaces-and-runtime
tags:
  - tui
  - textual
  - user-interface
  - widgets
---

# Modül: Terminal Kullanıcı Arayüzü (Terminal User Interface - TUI)

`Terminal Kullanıcı Arayüzü (TUI)`, teknik olmayan kullanıcılar için görsel, modern ve etkileşimli bir çalışma ortamı sunan Textual tabanlı arayüz bileşenidir (`src/tui.py`).

Tasarım hedefleri [[adr-004-hybrid-launcher-and-dual-ui]] belgesinde ele alınmıştır.

## Arayüz Düzeni ve Bileşen Hiyerarşisi

Arayüz kaydırma gerektirmeyen (non-scrolling) kompakt bir yerleşime sahiptir:

```text
┌─────────────────────────────────────────────────────────────┐
│ Kast 2.0 — Dublaj Çevirisi Kast Çıkarma Sistemi (Textual)   │
├─────────────────────────────────────────────────────────────┤
│ DOCX Senaryo Dosyası: [ /path/to/script.docx           ] [📂]│
│ Referans PDF (Opsiyonel): [                            ] [📂]│
├─────────────────────────────────────────────────────────────┤
│ Sıralama: (•) İlk Görünme Sırası  ( ) Replik Sayısı  ( ) A-Z│
│ Çıktı:    [ ] Orijinalin üzerine yaz (--in-place)            │
│           [ ] Yalnızca kast tablosunu kaydet (--standalone) │
├─────────────────────────────────────────────────────────────┤
│ [ Kast Tablosunu Çıkar ]       [ Temizle ]       [ Çıkış ]  │
├─────────────────────────────────────────────────────────────┤
│ Canlı İşlem Günlüğü (RichLog)                              │
│ [*] Döküman yükleniyor...                                  │
│ [+] 1089 replik, 14 karakter tespit edildi.                │
│ [✓] Başarıyla kaydedildi: /path/to/script_kast.docx         │
└─────────────────────────────────────────────────────────────┘
```

## Öne Çıkan Özellikler

### 1. Akıllı Sürükle-Bırak Temizliği (`clean_drag_drop_path`)
Kullanıcı masaüstünden bir dosyayı terminale sürükleyip bıraktığında işletim sisteminin eklediği tırnak işaretlerini (`"`, `'`), `file://` protokol öneklerini ve boşluk URL kodlamalarını (`%20`) anında temizleyerek saf dosya yoluna dönüştürür.

### 2. Yerel İşletim Sistemi Dosya Seçici Köprüsü (`select_file_dialog`)
`[📂]` butonuna tıklandığında kullanıcının işletim sistemine uygun grafiksel dosya seçici açılır:
- **Windows:** Kesintisiz Tkinter `filedialog` (varsa) veya arka plan PowerShell.
- **Linux:** Masaüstü ortamına göre `zenity` (GNOME) veya `kdialog` (KDE).
- **macOS:** AppleScript `osascript`.

### 3. Canlı İşlem Günlüğü (`RichLog`)
Arka plandaki [[headless-pdf-converter]] ve [[document-paginator]] adımları terminalde anlık olarak loglanır; işlem tamamlandığında yeşil onay mesajıyla özet gösterilir.

### 4. Karşılıklı Dışlama (Mutual Exclusivity)
`--in-place` ve `--standalone` bayraklarının aynı anda seçilmesi arayüz düzeyinde engellenir. Biri işaretlendiğinde diğeri otomatik olarak pasife alınır.

## İlgili Sayfalar

- [[hybrid-cli-dispatcher]]
- [[cross-platform-installers]]
- [[adr-004-hybrid-launcher-and-dual-ui]]
- [[cast-extraction-result]]
