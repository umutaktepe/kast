---
title: "İş Akışı: GitHub Actions Otomatik Windows Derleme ve Sürüm Dağıtımı"
type: workflow
status: active
date: 2026-09-23
domain: interfaces-and-runtime
tags:
  - ci-cd
  - github-actions
  - automation
  - release
  - windows
  - packaging
---

# İş Akışı: GitHub Actions Otomatik Windows Derleme ve Sürüm Dağıtımı

Kast 2.0 Windows Studio Edition, geliştiricilerin (Linux/macOS dahil) manuel ikili derleme yapmasına gerek kalmadan, tamamen otonom ve tekrarlanabilir bir CI/CD boru hattı üzerinden paketlenir ve GitHub Releases üzerinde yayınlanır (`.github/workflows/release-windows.yml`).

Bu iş akışı; PyInstaller bağımsız klasör demetini, taşınabilir (portable) ZIP arşivini, Inno Setup profesyonel kurulum sihirbazını ve kriptografik SHA256 sağlama toplamlarını sıfırdan oluşturur.

İlgili bileşenler ve mimari sayfalar: [[pyinstaller-standalone-packaging]], [[inno-setup-installer]], [[cross-platform-installers]] ve [[qt6-desktop-gui]].

---

## 1. Tetikleyiciler ve İzinler

İş akışı iki farklı senaryoda otomatik olarak tetiklenir:
1. **Etiket İtme (Tag Push):** Proje deposuna `v*` kalıbında bir Git etiketi itildiğinde (örn: `v2.1.0`).
2. **Manuel Tetikleme (`workflow_dispatch`):** GitHub Actions sekmesinden isteğe bağlı `version` girdisiyle (varsayılan: `'2.1.0'`).

GitHub Releases üzerinde yeni sürüm ve varlık (asset) oluşturabilmesi için `contents: write` iznine sahiptir.

---

## 2. Koşucu ve Boru Hattı Adımları

İş akışı temiz bir `windows-latest` sanal makinesinde `build-windows` işi altında şu adımları işletir:

1. **Depo Çekme (`actions/checkout@v4`):** `fetch-depth: 0` ile tüm Git geçmişi ve etiketler alınır.
2. **Sürüm Belirleme (PowerShell):** Tetikleyici türüne göre `VERSION` ortam değişkeni çözülür ve `$env:GITHUB_ENV` dosyasına yazılır (baştaki `v` harfi otomatik kırpılır).
3. **Python 3.11 Kurulumu (`actions/setup-python@v5`):** `cache: 'pip'` ile hızlı bağımlılık önbelleklemesi sağlanır.
4. **Bağımlılıkların Yüklenmesi:** `pip install --upgrade pip`, `requirements.txt`, `pyinstaller` ve `Pillow` kurulur.
5. **İkon Üretimi:** `python packaging/generate_icon.py` çalıştırılarak 7 çözünürlüklü `kast.ico` oluşturulur.
6. **PyInstaller Derlemesi:** `pyinstaller packaging/kast.spec --noconfirm` ile `dist/KastStudio/` klasör demeti üretilir.
7. **Taşınabilir ZIP Arşivi:** `Compress-Archive` komutu ile `dist/Kast-v<VERSION>-Windows-Portable.zip` sıkıştırılır (`Optimal` seviye).
8. **Inno Setup Kurulumu:** `choco install innosetup --no-progress -y` ile Inno Setup derleyicisi yüklenir.
9. **Kurulum Sihirbazı Derlemesi:** `iscc.exe /DMyAppVersion=%VERSION% packaging\installer.iss` ile `dist/Kast-v<VERSION>-Setup.exe` derlenir.
10. **SHA256 Sağlama Toplamları:** `Get-FileHash` ile her iki ikili dosyanın SHA256 özeti hesaplanarak `dist/checksums.txt` dosyasına yazılır.
11. **GitHub Release Yayınlama:** `softprops/action-gh-release@v2` eylemi ile kurulum dosyası, taşınabilir ZIP ve `checksums.txt` sürüm notlarıyla birlikte GitHub Releases'a yüklenir.

---

## 3. Dağıtım Çıktıları ve Varlıklar

Her başarılı yayında aşağıdaki 3 temel varlık yayımlanır:

| Dosya Adı | Açıklama |
| :--- | :--- |
| `Kast-v<VERSION>-Setup.exe` | Inno Setup kurulum sihirbazı (Word/LibreOffice tespiti ve masaüstü kısayolları) |
| `Kast-v<VERSION>-Windows-Portable.zip` | Kurulum gerektirmeyen, taşınabilir tam bağımsız stüdyo sürümü |
| `checksums.txt` | İndirilen dosyaların bütünlüğünü doğrulamak için SHA256 sağlama listesi |

---

## 4. Test ve Doğrulama Stratejisi

İş akışı dosyasının sözdizimi, YAML yapısı, izinleri, koşucu ortamı ve 11 kritik adımı `tests/test_ci_workflow.py` birim test takımı tarafından test edilir:
- `test_workflow_file_exists`: Dosya varlığı kontrolü.
- `test_workflow_syntax_and_triggers`: `push.tags` ve `workflow_dispatch` girdi doğrulaması.
- `test_workflow_permissions_and_runner`: `contents: write` ve `windows-latest` denetimi.
- `test_workflow_build_steps`: Tüm derleme, paketleme, Inno Setup ve yayınlama adımlarının sırası ve bayrakları.
- `test_workflow_step_shells`: PowerShell (`pwsh`) ve Command Prompt (`cmd`) kabuk ayrımı.
- `test_workflow_release_condition_and_naming`: Sürüm koşulları ve dinamik başlık formatı.

---

## 5. İlgili Sayfalar

- [[adr-006-windows-standalone-installer-and-ci]]
- [[inno-setup-installer]]
- [[pyinstaller-standalone-packaging]]
- [[cross-platform-installers]]
- [[qt6-desktop-gui]]
