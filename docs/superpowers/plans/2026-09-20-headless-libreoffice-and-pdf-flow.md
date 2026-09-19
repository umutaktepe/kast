# Headless LibreOffice and Direct PDF Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate dxpdf, establish a strict 100% exact pagination workflow using Headless LibreOffice/Word COM for background PDF conversion and direct user-supplied reference PDF processing, with automated installers ensuring LibreOffice is installed.

**Architecture:** Multi-tier 100% engine cascade: Direct user PDF if supplied -> Word COM on Windows -> Headless LibreOffice (`soffice`) on Linux/Windows/macOS -> Fail fast with clear error if no office suite is installed. Automated installation scripts (`install.sh`, `install.ps1`) handle installing LibreOffice if missing.

**Tech Stack:** Python 3.10+, LibreOffice (`soffice`), PowerShell Word COM, pdfplumber, Textual, Bash, PowerShell.

**Spec:** Brainstorming discussion on 2026-09-20 (strict 100% exact matching; no fallback to python layout approximation; direct PDF priority in TUI & CLI; automated LibreOffice installation in install scripts; elimination of dxpdf).

## Global Constraints

- Orijinal dökümandaki hiçbir metin, diyalog veya biçimlendirme bozulmamalıdır.
- `dxpdf` kütüphanesi fontconfig hataları ve 108pt hanging indent desteği olmaması nedeniyle tamamen kaldırılmalıdır.
- Asla tahmini mizanpaj motoruna (%93) sessiz fallback yapılmamalıdır; sayfa tespiti %100 doğrulukta PDF üzerinden yapılmalıdır.
- Kullanıcı TUI veya CLI üzerinden referans PDF verirse, arka planda DOCX dönüştürmek yerine doğrudan verilen PDF kullanılmalıdır.
- Kurulum scriptleri (`install.sh`, `install.ps1`) eksik LibreOffice durumunda otomatik kurulum yapmalı veya net şekilde yönlendirmelidir.

---

### Task 1: Dependency Cleanup and Headless LibreOffice Converter

**Files:**
- Modify: `requirements.txt`
- Modify: `src/pdf_converter.py`
- Modify: `tests/test_pdf_converter.py`

**Interfaces:**
- Consumes: None (system binaries `soffice`, `powershell`, Word COM)
- Produces: `find_soffice_binary() -> Optional[str]`, `is_pdf_conversion_supported() -> bool`, `convert_docx_to_pdf(docx_path: str, output_pdf_path: str) -> bool`, `temp_docx_to_pdf(docx_path: str) -> Generator[str, None, None]`, `PdfConversionError`

- [ ] **Step 1: Write the failing test for LibreOffice binary discovery and dxpdf removal**

Update `tests/test_pdf_converter.py` to test:
1. `find_soffice_binary()` on Linux and Windows paths.
2. `convert_docx_to_pdf()` executes `soffice --headless --convert-to pdf` when on Linux or Windows without MS Word.
3. Verify `dxpdf` is not imported or referenced anywhere in `pdf_converter.py`.
4. `temp_docx_to_pdf` raises `PdfConversionError` with actionable instruction when neither Word nor LibreOffice is present.

```python
def test_find_soffice_binary_search_paths():
    from src.pdf_converter import find_soffice_binary
    with patch("shutil.which", return_value="/usr/bin/soffice"):
        assert find_soffice_binary() == "/usr/bin/soffice"

def test_find_soffice_binary_windows_paths():
    from src.pdf_converter import find_soffice_binary
    with patch("sys.platform", "win32"), \
         patch("shutil.which", return_value=None), \
         patch("os.path.exists", side_effect=lambda p: p.endswith("soffice.exe")):
        assert find_soffice_binary() is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_pdf_converter.py -v`
Expected: FAIL (AttributeError or assertion failure because `find_soffice_binary` does not exist yet).

- [ ] **Step 3: Implement minimal code in `src/pdf_converter.py` and remove `dxpdf` from `requirements.txt`**

1. Remove `dxpdf>=0.8.0` from `requirements.txt`.
2. In `src/pdf_converter.py`:
   - Remove `import dxpdf`.
   - Implement `find_soffice_binary() -> Optional[str]` checking PATH (`shutil.which("soffice")`, `shutil.which("libreoffice")`), standard Windows directories (`ProgramFiles/LibreOffice/program/soffice.exe`, `LOCALAPPDATA/Programs/LibreOffice/program/soffice.exe`), and macOS (`/Applications/LibreOffice.app/Contents/MacOS/soffice`).
   - In `convert_docx_to_pdf()`:
     - Check Word COM on Windows first.
     - Check `find_soffice_binary()`: run `[soffice_path, "--headless", "--convert-to", "pdf", abs_docx, "--outdir", out_dir]`.
     - Handle moving output if necessary, return True on success.
   - In `temp_docx_to_pdf()`:
     - On failure, raise `PdfConversionError` with message:
       `"Kast'ın %100 doğrulukta sayfa tespiti yapabilmesi için sistemde LibreOffice veya Microsoft Word bulunmalıdır. Lütfen './install.sh' (Windows'ta '.\install.ps1') çalıştırın ya da LibreOffice yükleyin."`

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_pdf_converter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/pdf_converter.py tests/test_pdf_converter.py
git commit -m "feat(converter): dxpdf kaldirildi, headless libreoffice ve word com ile %100 hassasiyetli donusturucu eklendi"
```

---

### Task 2: Strict Pipeline and Direct PDF Flow Integration

**Files:**
- Modify: `kast.py`
- Modify: `src/tui.py`
- Modify: `tests/test_integration.py`

**Interfaces:**
- Consumes: `pdf_converter.temp_docx_to_pdf`, `paginator.process`
- Produces: `process_dubbing_script(docx_path, output_path=None, pdf_path=None, sort_by="appearance", standalone=False) -> str`

- [ ] **Step 1: Write integration tests verifying direct PDF priority and fail-fast when converter is absent**

In `tests/test_integration.py`:
1. Test: When `pdf_path` is passed, `temp_docx_to_pdf` is NOT called at all; `paginator.process` directly consumes `pdf_path`.
2. Test: When `pdf_path` is None, `temp_docx_to_pdf` is called.
3. Test: When `temp_docx_to_pdf` raises `PdfConversionError`, `process_dubbing_script` propagates it cleanly rather than falling back to approximate layout pagination.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_integration.py -v`
Expected: FAIL if existing tests expect dxpdf or mock differently.

- [ ] **Step 3: Update `kast.py` and `src/tui.py`**

1. In `kast.py`:
   - If `pdf_path`:
     Print log: `"[+] Verilen harici referans PDF doğrudan kullanılıyor: {pdf_path}"`
     Process: `assigned_paras = paginator.process(parsed_paras, pdf_path=pdf_path)`
   - Else:
     Print log: `"[+] Arka planda LibreOffice / Word ile geçici PDF üretiliyor..."`
     Use `with pdf_converter.temp_docx_to_pdf(docx_path) as temp_pdf:`
     Process: `assigned_paras = paginator.process(parsed_paras, pdf_path=temp_pdf)`
2. In `src/tui.py`:
   - In `action_extract()`:
     If `pdf_path`:
       `log.write(f"[bold green][*] Harici Referans PDF devrede (Doğrudan İşleniyor):[/bold green] {os.path.basename(pdf_path)}")`
     Else:
       `log.write("[bold cyan][*] Arka planda LibreOffice/Word motoru ile PDF üretiliyor...[/bold cyan]")`
   - Handle `PdfConversionError` cleanly and write formatted alert in the TUI RichLog.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_integration.py tests/test_tui.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kast.py src/tui.py tests/test_integration.py
git commit -m "feat(pipeline): dogrudan pdf onceligi ve kati 100% sayfalama garantisi"
```

---

### Task 3: Automated Installer Scripts for Linux and Windows

**Files:**
- Modify: `install.sh`
- Modify: `install.ps1`
- Create: `tests/test_install_scripts.py`

**Interfaces:**
- Consumes: OS package managers (`dnf`, `apt-get`, `pacman`, `zypper`, `winget`)
- Produces: Seamless automated installation of LibreOffice when missing

- [ ] **Step 1: Write test verifying installer detection logic**

In `tests/test_install_scripts.py`:
Verify that `install.sh` contains package manager detection for `dnf`, `apt-get`, `pacman`, `zypper` and checks `soffice`/`libreoffice`.
Verify that `install.ps1` contains check for Word COM / `soffice.exe` and fallback to `winget install TheDocumentFoundation.LibreOffice`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_install_scripts.py -v`
Expected: FAIL

- [ ] **Step 3: Update `install.sh` and `install.ps1`**

1. In `install.sh`:
   - Add Step 2.5: LibreOffice Kontrolü ve Kurulumu:
     ```bash
     if ! command -v soffice >/dev/null 2>&1 && ! command -v libreoffice >/dev/null 2>&1; then
         echo -e "${YELLOW}[!] Sistemde LibreOffice bulunamadı.${NC}"
         echo -e "${BLUE}➜${NC} %100 hassasiyetli sayfa tespiti için LibreOffice Writer kuruluyor..."
         if command -v dnf >/dev/null 2>&1; then
             sudo dnf install -y libreoffice-writer
         elif command -v apt-get >/dev/null 2>&1; then
             sudo apt-get update && sudo apt-get install -y libreoffice-writer
         elif command -v pacman >/dev/null 2>&1; then
             sudo pacman -S --noconfirm libreoffice-fresh
         elif command -v zypper >/dev/null 2>&1; then
             sudo zypper install -y libreoffice-writer
         else
             echo -e "${RED}[Uyarı] Paket yöneticisi otomatik tespit edilemedi. Lütfen 'libreoffice-writer' paketini manuel kurun.${NC}"
         fi
     else
         echo -e "${GREEN}✓${NC} LibreOffice tespit edildi."
     fi
     ```
2. In `install.ps1`:
   - Remove `dxpdf` check from line 43.
   - Add Step 3.5: LibreOffice / MS Word Kontrolü:
     - Check if Word COM object can be initialized.
     - Check if `soffice.exe` exists in PATH or `Program Files\LibreOffice`.
     - If neither exists:
       Check if `winget` is available and run:
       `winget install --id TheDocumentFoundation.LibreOffice -e --silent --accept-package-agreements --accept-source-agreements`

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_install_scripts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add install.sh install.ps1 tests/test_install_scripts.py
git commit -m "feat(installers): linux ve windows kurulum scriptlerine otomatik libreoffice yukleme eklendi"
```

---

### Task 4: Full End-to-End Verification

**Files:**
- Verify: Full test suite (`tests/`)
- Verify: `kast.py` CLI with reference PDF
- Verify: TUI launch and syntax check

- [ ] **Step 1: Run complete pytest suite**

Run: `.venv/bin/pytest`
Expected: ALL PASS

- [ ] **Step 2: Verify `kast.py` on `example/JACKIE & OOPJEN.docx` using `example/truekast.pdf`**

Run:
```bash
.venv/bin/python3 kast.py "example/JACKIE & OOPJEN.docx" --pdf "example/truekast.pdf"
```
Verify:
- Console reports direct reference PDF used.
- Output docx is generated.
- Characters and page numbers match `truekast.pdf` 100% (57/57 exact match).

- [ ] **Step 3: Commit any final polish**

```bash
git commit -m "chore: full pipeline verification passed"
```
