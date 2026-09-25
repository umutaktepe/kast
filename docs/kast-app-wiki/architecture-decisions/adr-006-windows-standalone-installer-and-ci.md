---
title: "ADR-006: Windows Bağımsız Paketleme (PyInstaller), Inno Setup Kurulum Sihirbazı ve GitHub Actions CI/CD Mimarisi"
type: architecture-decision-record
status: accepted
date: 2026-09-23
domain: architecture-decisions
tags:
  - adr
  - windows
  - packaging
  - pyinstaller
  - innosetup
  - ci-cd
  - github-actions
  - studio
---

# ADR-006: Windows Bağımsız Paketleme (PyInstaller), Inno Setup Kurulum Sihirbazı ve GitHub Actions CI/CD Mimarisi

## Bağlam (Context)

Kast 2.0 senaryo ve dublaj kast tablosu çıkarma sistemi, [[adr-005-qt6-windows-studio-gui]] kararı ile modern bir Qt6 grafik kullanıcı arayüzüne kavuşmuştur. Ancak uygulamanın Türkiye ve dünya genelindeki dublaj ve seslendirme stüdyolarında (çevirmenler, ses kayıt teknisyenleri, kast direktörleri) benimsenmesinin önündeki en büyük engel çalışma zamanı (runtime) bağımlılıklarıdır:

1. **Python ve Ortam Yönetimi Bariyeri:**
   - Hedef kullanıcı kitlesi yazılımcı veya sistem yöneticisi değildir.
   - Kullanıcıların bilgisayarlarına Python 3.10+ kurması, `PATH` ortam değişkenlerini yapılandırması, PowerShell veya CMD üzerinde yürütme ilkelerini (`ExecutionPolicy`) yönetmesi, sanal ortam (`.venv`) kurması ve `pip` paketlerini derlemesi pratik olarak imkansız veya çok yüksek sürtünmelidir.
2. **Ofis ve Sayfalama Bağımlılığı Riski:**
   - Kast'ın kesin sayfa numarası üretme mimarisi ([[adr-002-strict-pdf-pagination-flow]], [[headless-pdf-converter]]), dökümanların arka planda Microsoft Word COM nesnesi veya LibreOffice (`soffice`) motoru ile dönüştürülmesine dayanır.
   - Word lisansı bulunmayan veya LibreOffice kurulu olmayan bir sistemde kullanıcıya teknik hata fırlatmak yerine kurulum esnasında bu ihtiyacın sessizce ve otomatik olarak giderilmesi gerekmektedir.
3. **Çoklu Platform Geliştirme ve Dağıtım Zorluğu:**
   - Kast çekirdeğini geliştiren mühendisler Linux veya macOS üzerinde çalışabilmektedir. Her yeni sürüm çıktığında yerel bir Windows makinesinde manuel `.exe` derlemesi yapmak sürdürülebilir değildir.
   - Dağıtılan ikililerin güvenilirliği, tekrarlanabilirliği ve kriptografik doğrulanabilirliği (SHA256) için bulut tabanlı tam otomatik bir derleme ve yayın hattı şarttır.

## Karar (Decision)

Kast 2.0'ın Windows dağıtım mimarisi için sıfır bağımlılık prensibi benimsenmiş; **PyInstaller**, **Inno Setup 6** ve **GitHub Actions** üçlüsünden oluşan entegre bir yayın mimarisi kurulmuştur:

1. **Klasör Demeti Modunda PyInstaller Paketlemesi (`COLLECT`):**
   - `packaging/kast.spec` yapılandırması ile `dist/KastStudio/` klasör demeti üretilir ([[pyinstaller-standalone-packaging]]).
   - `run_gui.py` giriş noktası üzerinden `console=False` (`--noconsole`) ile çalıştırılarak Windows konsol pencereleri izole edilir.
   - `packaging/generate_icon.py` aracı ile 7 farklı çözünürlükte (`16x16`'dan `256x256`'ya) Windows uyumlu çoklu DPI stüdyo ikonu (`kast.ico`) üretilir ve ikiliye gömülür.
   - Tek parça exe (`--onefile`) yerine klasör demeti seçilerek açılış gecikmesi (startup latency) sıfırlanmış ve antivirüs sahte pozitifleri (false positives) asgariye indirilmiştir.
2. **Inno Setup 6 Kurulum Sihirbazı (`installer.iss`):**
   - Windows 10/11 x64 platformlarını hedefleyen modern kurulum sihirbazı (`Kast-vX.Y.Z-Setup.exe`) geliştirilmiştir ([[inno-setup-installer]]).
   - Kurulum `{autopf}\Kast Studio` dizinine yapılır; Başlat Menüsü, Masaüstü kısayolları ve Windows Denetim Masası Program Ekle/Kaldır entegrasyonu sağlanır.
   - Türkçe ve İngilizce çift dil desteği sunulur.
3. **Akıllı Pascal Script ile Sessiz Ofis Denetimi (`[Code]`):**
   - Kurulum esnasında `IsWordInstalled()` ve `IsLibreOfficeInstalled()` fonksiyonları kayıt defteri (Registry) ve dosya sistemini tarar.
   - Eğer Microsoft Word veya LibreOffice varsa ek hiçbir işlem yapılmaz.
   - Eğer sistemde **İKİSİ DE YOKSA**, `CurStepChanged(ssPostInstall)` adımında arka planda sessizce:
     - 1. Öncelik: `winget install --id TheDocumentFoundation.LibreOffice -e --silent` komutunu gizli pencerede çalıştırır.
     - 2. Öncelik: `winget` yoksa PowerShell aracılığıyla resmi LibreOffice MSI paketini indirir ve `msiexec /i ... /qn /norestart` ile sessizce kurar.
   - Böylece son kullanıcı teknik ayrıntılarla karşılaşmadan döküman sayfalama altyapısı eksiksiz hazırlanmış olur.
4. **Taşınabilir Taşınabilir Sürüm (Portable ZIP):**
   - Yönetici yetkisi bulunmayan veya kurulum yapmak istemeyen stüdyolar için `dist/KastStudio/` dizini doğrudan `Kast-vX.Y.Z-Windows-Portable.zip` olarak paketlenir.
5. **GitHub Actions Tam Otomatik CI/CD Boru Hattı (`release-windows.yml`):**
   - `windows-latest` sanal makinesinde `v*` git etiketi veya manuel tetikleme (`workflow_dispatch`) ile çalışır ([[github-actions-release-workflow]]).
   - Python 3.11 ortamı kurar, bağımlılıkları çeker, ikonları üretir, PyInstaller ile derler, Portable ZIP sıkıştırır, Chocolatey ile Inno Setup kurup Setup.exe üretir, SHA256 özetlerini (`checksums.txt`) hesaplar ve `softprops/action-gh-release@v2` ile GitHub Releases üzerinde yayımlar.

## Alternatifler (Alternatives Considered)

- **Alternatif 1: Tek Dosya PyInstaller Exe (`--onefile`):**
  - *Değerlendirme:* Tek bir çalıştırılabilir dosya dağıtım açısından derli toplu görünür.
  - *Reddedilme Gerekçesi:* `--onefile` modu, program her açıldığında 60-80 MB'lık Python çalışma zamanını ve Qt6 kütüphanelerini `%TEMP%` klasörüne ayıklar. Bu durum açılışta 5-10 saniyelik gecikme yaratır. Ayrıca stüdyo bilgisayarlarındaki kurumsal antivirüs yazılımları geçici dizinden çalışan ikilileri sıklıkla şüpheli görüp karantinaya almaktadır.
- **Alternatif 2: MSIX / Windows Mağazası (Microsoft Store):**
  - *Değerlendirme:* Modern Windows 10/11 uygulama dağıtım formatıdır.
  - *Reddedilme Gerekçesi:* Yıllık ücretli kod imzalama sertifikaları (Code Signing Certificate), Microsoft Geliştirici hesabı ve katı UWP/AppContainer sandbox kısıtlamaları gerektirir. Bu sandbox yapısı yerel Word COM nesnelerine erişimi ve sessiz LibreOffice entegrasyonunu engeller.
- **Alternatif 3: Nullsoft Scriptable Install System (NSIS):**
  - *Değerlendirme:* Açık kaynaklı ve hafif bir kurulum oluşturucudur.
  - *Reddedilme Gerekçesi:* NSIS betik dili C/assembly benzeri karmaşık bir sözdizimine sahiptir; Registry tarama, COM nesnesi denetimi, `winget` yürütme ve PowerShell MSI fallback senaryolarında Inno Setup'ın Pascal Scripting (`[Code]`) esnekliğine, okunabilirliğine ve modern arayüz kararlılığına sahip değildir.
- **Alternatif 4: Geliştirici Makinesinde Yerel Manuel Derleme:**
  - *Değerlendirme:* CI/CD kurmadan yerel Windows bilgisayarda `pyinstaller` ve `iscc` çalıştırmak.
  - *Reddedilme Gerekçesi:* macOS ve Linux kullanan geliştiricilerin sürüm çıkarmasını engeller. Tekrarlanabilirlik düşüktür; geliştiricinin yerel ortamındaki artık paketler ve sürüm uyumsuzlukları sürüme sızabilir.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- **Sıfır Ön Koşul (Zero-Prerequisites):** Windows kullanıcıları Python, terminal veya paket yöneticisi kurmadan doğrudan çift tıklamayla Kast Studio'yu kullanmaya başlar.
- **Kesintisiz Sayfalama Garantisi:** Akıllı ofis tespiti sayesinde Word ve LibreOffice eksikliği otomatik giderilir, sayfalama motorunun çalışması garanti altına alınır.
- **Yüksek Performans:** Klasör demeti mimarisi sayesinde uygulama gecikmesiz, anında açılır.
- **Tam Otonom Sürüm Yönetimi:** Geliştiriciler yerel işletim sisteminden bağımsız olarak tek bir `git tag` ile 5-10 dakika içinde Setup, Portable ZIP ve SHA256 doğrulama dosyalarını yayımlayabilir.
- **Esnek Dağıtım Seçenekleri:** Hem tam sistem kurulumu (`Setup.exe`) hem de taşınabilir USB/klasör sürümü (`Portable.zip`) aynı anda sunulur.

### Olumsuz / Kısıtlar:
- **Paket Boyutu:** Gömülü Python çalışma zamanı ve PySide6 kütüphaneleri sebebiyle kurulum paketi yaklaşık 60-80 MB boyutundadır (stüdyo iş istasyonları için önemsizdir).
- **Kod İmzalama (Code Signing) Bildirimi:** Açık kaynaklı bir proje olduğundan pahalı ticari EV/OV sertifikası bulunmamaktadır; Windows SmartScreen ilk çalıştırmada "Bilinmeyen Yayıncı" uyarısı gösterebilir (kullanıcı "Yine de çalıştır" diyerek devam eder).

## İlgili Sayfalar

- [[inno-setup-installer]]
- [[pyinstaller-standalone-packaging]]
- [[github-actions-release-workflow]]
- [[cross-platform-installers]]
- [[qt6-desktop-gui]]
- [[adr-005-qt6-windows-studio-gui]]
- [[headless-pdf-converter]]
