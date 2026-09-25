---
title: "Modül: Hibrit Komut Satırı Yönlendiricisi (Hybrid CLI Dispatcher)"
type: module
domain: interfaces-and-runtime
tags:
  - cli
  - dispatcher
  - arguments
  - entrypoint
---

# Modül: Hibrit Komut Satırı Yönlendiricisi (Hybrid CLI Dispatcher)

`Hibrit Komut Satırı Yönlendiricisi`, projenin ana giriş noktası olan `kast.py` dosyasıdır. Kullanıcının çalıştırma şekline göre TUI ve CLI modları arasında akıllıca geçiş yapar ve senaryo işleme boru hattını orkestre eder.

Mimari temelleri [[adr-004-hybrid-launcher-and-dual-ui]] belgesinde özetlenmiştir.

## Karar Ağacı ve Başlatma Mantığı

```python
# GUI modu talep edildiyse Qt6 Studio arayüzünü aç
if args.gui_mode:
    from src.gui import launch_gui
    return launch_gui()

# Argümansız çağrıldığında veya --tui verildiğinde TUI aç
should_launch_tui = args.tui_mode or (not raw_argv and not args.cli_mode)
if should_launch_tui:
    from src.tui import launch_tui
    return launch_tui()
```

- **`kast --gui` veya `kast -g`:** Doğrudan [[qt6-desktop-gui]] (Qt6 Modern Stüdyo Arayüzü) açılır.
- **`kast` (Argümansız):** Doğrudan [[terminal-user-interface]] açılır.
- **`kast dosya.docx [bayraklar]`:** TUI/GUI arayüzü başlatılmadan komut satırı boru hattı çalıştırılır.

## Komut Satırı Argümanları

| Bayrak | Kısayol | Tür / Değerler | Açıklama |
| :--- | :---: | :--- | :--- |
| `docx_file` | - | Dosya Yolu (Konumsal) | İşlenecek dublaj senaryosu DOCX dosyasının yolu. |
| `-o`, `--output` | `-o` | Dosya Yolu | Çıktı dosyasının kaydedileceği özel yol (varsayılan: `<dosya>_kast.docx`). |
| `--gui` | `-g` | Bayrak (Boolean) | Modern Qt6 Masaüstü Stüdyo Arayüzünü (GUI) başlatır. |
| `--sort` | - | `appearance`, `count`, `name` | Karakter sıralama modu (varsayılan: `appearance`). |
| `--count` | `-c` | Bayrak (Boolean) | Replik sayısına göre çoktan aza sırala (`--sort count` kısayolu). |
| `--name` | `-n` | Bayrak (Boolean) | Karakter adına göre alfabetik sırala (`--sort name` kısayolu). |
| `--in-place` | - | Bayrak (Boolean) | Kast tablosunu yeni dosya yerine orijinal dosyanın sonuna yazar. |
| `--pdf` | - | Dosya Yolu | Sayfa tespiti için kullanıcı tarafından sağlanan referans PDF. |
| `--standalone` | - | Bayrak (Boolean) | Orijinal metni içermeyen, sadece kast tablosunun olduğu yeni belge üretir. |
| `--tui` | `-t` | Bayrak (Boolean) | TUI görsel arayüzünü zorla açar. |
| `--cli` | - | Bayrak (Boolean) | Argüman olmasa dahi TUI açılmasını engelleyip terminal yönlendirmesi ister. |

## Boru Hattı Akışı (`process_cast_document`)

1. [[dubbing-docx-parser]] ile paragraflar diyalog, süre kodu ve başlık olarak ayrıştırılır.
2. Varsa `--pdf` kullanılır; yoksa [[headless-pdf-converter]] ile geçici PDF üretilir.
3. [[document-paginator]] paragraflara kesin sayfa numaralarını atar.
4. [[character-stats]] ve [[cast-extraction-result]] nesneleri derlenir.
5. İstenen sıralama (`appearance`, `count`, `name`) uygulanır.
6. [[cast-table-writer]] ile kast tablosu Word dökümanına eklenir ve kaydedilir.

## Birleşik Dosya Yönlendiricisi (`process_dubbing_file`)

Kast 2.0 masaüstü stüdyo GUI ve arka plan iş parçacıkları (`ExtractionWorker`) için hem `.docx` hem `.pdf` senaryolarını tek bir API üzerinden yöneten birleşik yönlendirici fonksiyonudur:

- **PDF Girişi (`.pdf`):** Doğrudan [[dubbing-pdf-parser]] motorunu ve `process_pdf_document` akışını çağırır. PDF dosyalarının üzerine doğrudan Word tablosu yazılamayacağı için `in_place=True` durumunda `ValueError` fırlatır. Sayfa bazında `progress_callback(pct, msg)` ile ilerleme bildirir.
- **DOCX Girişi (`.docx`):** Orijinal `process_cast_document` akışını ve sayfalama motorunu çalıştırır; replik sayımı ve `CastExtractionResult` istatistiği oluşturur.
- **Çıktı Sözleşmesi:** `(output_file_path: str, result: CastExtractionResult)` demeti döndürür.

## İlgili Sayfalar

- [[terminal-user-interface]]
- [[qt6-desktop-gui]]
- [[dubbing-docx-parser]]
- [[dubbing-pdf-parser]]
- [[document-paginator]]
- [[cast-table-writer]]
- [[adr-004-hybrid-launcher-and-dual-ui]]
- [[adr-005-qt6-windows-studio-gui]]

