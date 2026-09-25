---
title: "Modül: PyInstaller Bağımsız Paketleme ve İkon Üretici"
type: module
status: active
date: 2026-09-23
domain: interfaces-and-runtime
tags:
  - packaging
  - pyinstaller
  - windows
  - icon
  - gui
---

# Modül: PyInstaller Bağımsız Paketleme ve İkon Üretici

Kast 2.0 Windows Studio Edition, son kullanıcının sisteminde Python veya ek bağımlılıklar bulunmasını gerektirmeyen, doğrudan çift tıklamayla çalışan bağımsız bir Windows dağıtımı (`dist/KastStudio/`) olarak paketlenir.

Tasarım kararları ve kullanıcı arayüzü temeli [[qt6-desktop-gui]], [[adr-005-qt6-windows-studio-gui]], [[inno-setup-installer]], [[github-actions-release-workflow]] ve [[cross-platform-installers]] sayfalarıyla ilişkilidir.

---

## 1. Bileşenler ve Paketleme Mimarisi

| Dosya | Görev ve Sorumluluk |
| :--- | :--- |
| `packaging/generate_icon.py` | Kullanıcı PNG/JPEG logosundan veya yerleşik geometrik stüdyo temasından 7 çözünürlüklü (`16x16` - `256x256`) Windows `.ico` dosyası üreten CLI ve modül aracı. |
| `packaging/run_gui.py` | Windows konsol penceresi açılmadan doğrudan `launch_gui()` fonksiyonunu çağıran izole PyInstaller giriş noktası. |
| `packaging/kast.spec` | PyInstaller için klasör demeti (`COLLECT`, `dist/KastStudio`), veri dosyaları (`docs/`, `example/`, `packaging/assets/`), gizli bağımlılıklar (`PySide6`, `docx`, `pdfplumber`, `pypdf`, `PIL`) ve gereksiz kütüphane dışlamalarını (`tkinter`, `matplotlib`, `scipy`) yapılandıran spec dosyası. |
| `packaging/assets/` | Resmi `kast_icon.png` ve derleme aşamasında üretilen `kast.ico` varlıklarını barındıran dizin. |

---

## 2. Çoklu Çözünürlüklü İkon Üretimi (`generate_icon.py`)

Windows dosya yöneticisi (Explorer), görev çubuğu ve pencere başlıkları farklı DPI ve boyutlarda ikonlara ihtiyaç duyar. `generate_icon.py` aracı şu boyutları tek bir `.ico` dosyasında birleştirir:
`[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]`

- **Kaynak Varlığı:** `packaging/assets/kast_icon.png` mevcutsa `PIL.Image` ile RGBA'ya çevrilir, `Image.Resampling.LANCZOS` filtresiyle örneklenir ve ICO formatında kaydedilir.
- **Geometrik Fallback:** Kaynak resim bulunamadığında sistem çökmez; stüdyo paletine uygun gece mavisi dairesel zemin (`#0f172a`), camgöbeği dış çerçeve (`#38bdf8`) ve 'K' harfi motifi çizilerek dinamik ikon üretilir.
- **CLI Kullanımı:**
  ```bash
  python packaging/generate_icon.py --source packaging/assets/kast_icon.png --output packaging/assets/kast.ico
  ```

---

## 3. GUI Giriş Noktası ve Konsol İzolasyonu (`run_gui.py`)

Windows ortamında konsolsuz pencere başlatmak için `console=False` (`--noconsole`) ayarı gereklidir. `run_gui.py`:
- `ROOT_DIR` yolunu `sys.path` başına ekleyerek modül çözümlemesini garanti eder.
- `src.gui.launch_gui` fonksiyonunu çağırır ve dönen Qt çıkış kodunu `sys.exit` ile işletim sistemine iletir.

---

## 4. PyInstaller Spec Yapılandırması (`kast.spec`)

`packaging/kast.spec`:
- **Giriş:** `run_gui.py`
- **Veriler (`datas`):** `docs/`, `example/`, `packaging/assets/`
- **Gizli İçe Aktarmalar (`hiddenimports`):** `PySide6.QtCore`, `PySide6.QtGui`, `PySide6.QtWidgets`, `docx`, `pdfplumber`, `pypdf`, `PIL`
- **Hariç Tutulanlar (`excludes`):** Paket boyutunu küçültmek ve açılış hızını artırmak için kullanılmayan `tkinter`, `matplotlib`, `scipy`, `notebook`, `IPython` modülleri dışlanır.
- **EXE Ayarları:** `name="KastStudio"`, `console=False`, `icon="packaging/assets/kast.ico"`
- **Demetleme:** `COLLECT` ile taşınabilir klasör mimarisi oluşturulur.

---

## 5. İlgili Sayfalar

- [[adr-006-windows-standalone-installer-and-ci]]
- [[inno-setup-installer]]
- [[github-actions-release-workflow]]
- [[qt6-desktop-gui]]
- [[cross-platform-installers]]
- [[adr-005-qt6-windows-studio-gui]]
- [[hybrid-cli-dispatcher]]
