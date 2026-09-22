---
title: "ADR-002: %100 Kesin Sayfalama Akışı ve Headless LibreOffice Entegrasyonu"
type: architecture-decision-record
status: accepted
date: 2026-09-20
domain: architecture-decisions
tags:
  - adr
  - pagination
  - libreoffice
  - word-com
  - dxpdf
---

# ADR-002: %100 Kesin Sayfalama Akışı ve Headless LibreOffice Entegrasyonu

## Bağlam (Context)

Dublaj kast tablosunun en kritik sütunlarından biri `Repliklerin Geçtiği Sayfalar`dır. Seslendirme yönetmeni ve teknisyeni, kayıt sırasında bir oyuncunun hangi sayfalarda repliği olduğunu tam olarak bilmek zorundadır. Bir sayfanın yanlış tespit edilmesi stüdyo kayıt seansında zaman kaybına ve operasyonel aksaklıklara yol açar.

Projenin ilk sürümlerinde sayfa tespiti için saf Python mizanpaj simülasyonu (`PurePythonLayoutPaginator`) geliştirilmişti. Bu motor Word kenar boşlukları, satır aralığı (1.5) ve Pillow `ImageFont` metrikleriyle satır sarma simülasyonu yapıyordu. Ancak bu yöntem tipografik mikro-farklar ve harici font hiyerarşileri nedeniyle ~%90-93 doğruluk seviyesinde kalıyor, Word'ün gerçek sayfalama motorunun birebir yerini tutamıyordu.

Bu sorunu çözmek için `dxpdf` (Rust + Skia tabanlı bağımsız DOCX $\rightarrow$ PDF dönüştürücüsü) denendi. Ancak `dxpdf` entegrasyonu iki büyük kusur sergiledi:
1. Linux sistemlerde fontconfig kitaplığı ile çakışarak çökme yaşatması.
2. Dublaj şablonlarındaki standart **108pt (1.5 inç) asılı girinti (hanging indent)** desteğini doğru render edememesi ve sayfa taşmalarında kaymalara sebep olması.

## Karar (Decision)

Tahmini simülatörlere ve eksik render motorlarına sessiz geri dönüş (silent fallback) yapılması kesin olarak yasaklanmış ve **Sıfır Hata / %100 Kesin Sayfalama (Strict 100% Fidelity)** mimarisi kabul edilmiştir:

1. **Öncelik 1 (Kullanıcı Tarafından Sağlanan PDF):** Kullanıcı CLI (`--pdf`) veya TUI üzerinden senaryonun PDF çıktısını sağlarsa, hiçbir dönüştürme yapılmadan doğrudan [[pdf-matching-engine]] devreye girer.
2. **Öncelik 2 (Windows Yerel Word COM):** Windows işletim sisteminde PowerShell üzerinden `Word.Application` COM arayüzü tetiklenerek DOCX, Word'ün kendi motoruyla geçici PDF'e dönüştürülür.
3. **Öncelik 3 (Headless LibreOffice - `soffice`):** Linux, macOS ve Word bulunmayan sistemlerde sistemdeki `soffice --headless --convert-to pdf` ikili dosyası arka planda çalıştırılarak geçici PDF üretilir.
4. **Fail-Fast Prensibi (`PdfConversionError`):** Sistemde ne Word ne de LibreOffice bulunamazsa ve kullanıcı harici PDF vermediyse, asla tahmini motora sessiz fallback yapılmaz; işlem derhal durdurularak kullanıcıya yükleme komutlarını (`./install.sh` veya `.\install.ps1`) gösteren açıklayıcı bir `PdfConversionError` fırlatılır.
5. **Otomatik Geçici Dosya Temizliği:** [[headless-pdf-converter]] içindeki `temp_docx_to_pdf` bağlam yöneticisi (context manager), işlem başarılı olsa da hata alsa da `finally:` bloğunda geçici PDF'i diskten siler.

## Alternatifler (Alternatives Considered)

- **Alternatif 1: Saf Python Mizanpaj Motoruna Güvenmek:**
  - *Reddedilme Gerekçesi:* %90 doğruluk profesyonel stüdyo kaydı için yetersizdir. Yönetmenin 1 sayfa sapmayla aktörü yanlış sayfada araması kabul edilemez bir hatadır.
- **Alternatif 2: `dxpdf` Python Kütüphanesi:**
  - *Reddedilme Gerekçesi:* 108pt hanging indent render edememesi ve fontconfig çöküşleri nedeniyle `requirements.txt`'den tamamen çıkarılmıştır.
- **Alternatif 3: Bulut Tabanlı Dönüştürme API'leri:**
  - *Reddedilme Gerekçesi:* Gizlilik sözleşmeleri (NDA) altındaki yayınlanmamış film senaryolarının harici bir sunucuya yüklenmesi telif ve güvenlik açısından kesinlikle yasaktır. Çözüm tamamen yerel (on-device) olmalıdır.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- Sayfa tespitinde %100 kesin Word mizanpaj doğruluğu garanti altına alındı.
- Gizli veya tahmin edilmiş sayfa numaraları riski sıfırlandı.
- Kurulum betikleri (`install.sh`, `install.ps1`) eksik LibreOffice durumunda otomatik paket kurulumunu üstlendi.

### Olumsuz / Kısıtlar:
- Çevrimdışı ve Word bulunmayan Linux sunucularda `libreoffice-writer` paketinin sistem düzeyinde kurulu olması zorunlu hale geldi.

## İlgili Sayfalar

- [[headless-pdf-converter]]
- [[pdf-matching-engine]]
- [[document-paginator]]
- [[pure-python-layout-paginator]]
- [[cross-platform-installers]]
