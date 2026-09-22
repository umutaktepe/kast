---
title: "Modül: Headless PDF Dönüştürücü (Headless PDF Converter)"
type: module
domain: pagination-subsystem
tags:
  - pdf-converter
  - libreoffice
  - word-com
  - automation
---

# Modül: Headless PDF Dönüştürücü (Headless PDF Converter)

`Headless PDF Dönüştürücü`, dublaj senaryosu DOCX dosyalarını arka planda kullanıcı müdahalesi olmadan ve görünmez şekilde yüksek çözünürlüklü PDF formatına dönüştüren altyapı modülüdür (`src/pdf_converter.py`).

Bu modül, [[adr-002-strict-pdf-pagination-flow]] kararında belirlenen sıfır hata ve %100 doğruluk prensibinin teknik omurgasıdır.

## İkili Arama ve Platform Stratejisi

### 1. `find_soffice_binary() -> Optional[str]`
LibreOffice ikili dosyasını (`soffice` veya `libreoffice`) işletim sistemine göre arar:
- **PATH:** `shutil.which("soffice")`, `shutil.which("libreoffice")`.
- **Windows Standart Dizinleri:** `%ProgramFiles%\LibreOffice\program\soffice.exe`, `%ProgramFiles(x86)%`, `%LOCALAPPDATA%\Programs`.
- **macOS:** `/Applications/LibreOffice.app/Contents/MacOS/soffice`.

### 2. `convert_docx_to_pdf(docx_path: str, output_pdf_path: str) -> bool`
- **Windows Üzerinde:** PowerShell üzerinden yerel Microsoft Word COM nesnesi (`New-Object -ComObject Word.Application`) çağrılır. Word yüklüyse Microsoft'un kendi render motoruyla dönüşüm gerçekleştirilir (`WdSaveFormat::wdFormatPDF = 17`).
- **Linux, macOS ve Word Olmayan Sistemlerde:** `soffice --headless --convert-to pdf` komutu izole bir geçici dizin altında çalıştırılır ve üretilen PDF hedef yola taşınır.

## Güvenli Geçici Dosya Yönetimi (`temp_docx_to_pdf`)

Kast, diskte artık veya geçici dosya bırakmamayı garanti eden Python bağlam yöneticisi (context manager) modelini uygular:

```python
@contextmanager
def temp_docx_to_pdf(docx_path: str) -> Generator[str, None, None]:
    temp_pdf_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_pdf_path = f.name

        success = convert_docx_to_pdf(docx_path, temp_pdf_path)
        if not success or not os.path.exists(temp_pdf_path) or os.path.getsize(temp_pdf_path) == 0:
            raise PdfConversionError(
                "Kast'ın %100 doğrulukta sayfa tespiti yapabilmesi için sistemde LibreOffice veya Microsoft Word bulunmalıdır. "
                "Lütfen './install.sh' (Windows'ta '.\\install.ps1') çalıştırın ya da LibreOffice yükleyin."
            )
        yield temp_pdf_path
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except OSError:
                pass
```

## Hata Yönetimi (`PdfConversionError`)

Sistemde dönüştürücü bulunamazsa ya da dönüşüm başarısız olursa, tahmini motora sessiz fallback yapılmaz; doğrudan kullanıcıyı yönlendiren `PdfConversionError` fırlatılır.

## İlgili Sayfalar

- [[document-paginator]]
- [[pdf-matching-engine]]
- [[cross-platform-installers]]
- [[adr-002-strict-pdf-pagination-flow]]
