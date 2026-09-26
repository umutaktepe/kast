---
title: "ADR-008: Uygulama İçi GitHub Releases Güncelleme Motoru, Dağıtım Paketi Tespiti ve Windows Dosya Kilidi Çözümü"
type: architecture-decision-record
status: accepted
date: 2026-09-26
domain: architecture-decisions
tags:
  - adr
  - updater
  - github-releases
  - auto-update
  - windows
  - portable
  - innosetup
  - qt6
  - pyinstaller
---

# ADR-008: Uygulama İçi GitHub Releases Güncelleme Motoru, Dağıtım Paketi Tespiti ve Windows Dosya Kilidi Çözümü

## Bağlam (Context)

Kast Studio masaüstü uygulaması ([[adr-005-qt6-windows-studio-gui]], [[adr-006-windows-standalone-installer-and-ci]]), Türkiye ve dünya genelindeki dublaj stüdyolarında hem tam sistem kurulumu (Inno Setup `Setup.exe`) hem de taşınabilir dizin (PyInstaller `Portable.zip`) olarak kullanılmaktadır. Ancak yeni sürümler, kritik hata düzeltmeleri ve kural seti güncellemeleri yayınlandığında son kullanıcıların güncellemelerden haberdar olması ve yeni sürümü kurması ciddi operasyonel zorluklar barındırmaktaydı:

1. **Manuel Takip Sürtünmesi:**
   - Dublaj çevirmenleri ve ses kayıt teknisyenleri GitHub deposunu veya sürümler sayfasını düzenli takip etmemektedir. Uygulamanın yeni bir sürüm çıktığında bunu kullanıcıya proaktif olarak bildirmesi şarttır.
2. **Kullanıcı İradesine Saygı ve Sessiz Açılış:**
   - Otomatik zorunlu güncellemeler veya açılışta beliren engelleyici (blocking) bildirimler, stüdyoda acil senaryo teslimi yapan kullanıcıların iş akışını kesintiye uğratabilir. Güncelleme denetimi arka planda asenkron çalışmalı, kullanıcı istediğinde güncellemeyi erteleyebilmeli veya göz ardı edebilmelidir.
3. **Farklı Dağıtım Türleri (Setup vs. Portable):**
   - Windows ortamında bazı kullanıcılar uygulamayı `Program Files` dizinine Inno Setup sihirbazıyla kurarken, yönetici yetkisi olmayan stüdyo personeli taşınabilir `Portable.zip` paketini masaüstünden veya USB bellekten çalıştırmaktadır.
   - Her iki dağıtım türünün güncelleme mantığı ve hedef indirme paketi farklıdır; sistemin hangi paketten çalıştığını otonom olarak algılaması gerekir.
4. **Windows Çalışan Dosya Kilidi (`ERROR_ACCESS_DENIED`):**
   - Windows işletim sisteminde çalışan bir `.exe` dosyasının veya onun kilitlediği DLL'lerin üzerine doğrudan yazma yapılamaz (`Access Violation / File Lock`). Güncelleme indirildikten sonra mevcut uygulamanın kendini kilitlemeden kapatması ve kurulum/üzerine yazma işlemini güvenle işletim sistemine devretmesi zorunludur.
5. **Sıfır Ek Dış Bağımlılık Prensibi:**
   - Güncelleme denetimi ve indirme motoru için dış kütüphaneler (örneğin `requests`, `urllib3`, `aiohttp`, `pywin32`) eklenmemeli; standart Python kütüphaneleri (`urllib.request`, `zipfile`, `tempfile`, `subprocess`) ve mevcut PySide6 araçları kullanılmalıdır.

## Karar (Decision)

Kast Studio için tam entegre, asenkron ve dağıtım türüne duyarlı bir GitHub Releases güncelleme mimarisi benimsenmiştir:

1. **GitHub Releases REST API Entegrasyonu ve Semantik Karşılaştırma (`src/version.py`, `src/updater.py`):**
   - Depo adresi `https://api.github.com/repos/umutaktepe/Kast/releases/latest` üzerinden sorgulanır.
   - `src/version.py` içinde `__version__ = "2.1.1"` kanonik sürümü tanımlanmış; ön ek temizleme (`v2.1.2` -> `(2, 1, 2)`) ve `is_newer_version(latest, current)` karşılaştırması semantik sürümleme kurallarıyla doğrulanmıştır.
2. **Otonom Dağıtım Türü Tespiti (`DistributionType`):**
   - `detect_distribution_type()` fonksiyonu `sys.frozen` ve çalıştırılabilir dosyanın bulunduğu dizini (`sys.executable`) inceler:
     - Dizin içinde `unins000.exe` (Inno Setup kaldırıcı izi) mevcutsa dağıtım `DistributionType.SETUP` olarak sınıflandırılır.
     - `sys.frozen == True` ancak `unins000.exe` yoksa dağıtım `DistributionType.PORTABLE` olarak sınıflandırılır.
     - Donmamış Python yorumlayıcısında çalışıyorsa `DistributionType.DEV` döner.
   - Hedef paket seçiminde (`select_target_asset`): Setup dağıtımı için `*Setup.exe` varlığı, Portable için `*Portable.zip` veya `*.zip` varlığı taranarak doğru indirme URL'si seçilir.
3. **PySide6 Asenkron İş Parçacıkları ve Koyu Temalı Diyaloglar (`src/updater_gui.py`):**
   - `UpdateCheckWorker(QThread)`: Ağ isteklerini GUI thread'ini dondurmadan arka planda yürütür.
   - `UpdateDownloadWorker(QThread)`: Dosya indirme işlemini bloklar halinde (chunked) yürütür; `download_progress(received_bytes, total_bytes)` sinyali ile yüzde ve aktarım hızını arayüze aktarır.
   - `UpdateNotificationDialog`: StudioTheme koyu paletine uygun, yeni sürüm etiketini, mevcut sürümü ve sürüm notlarını (Release Notes) gösteren diyalog. "Güncelle" ve "Daha Sonra" butonları ile kullanıcı iradesi korunur.
   - `UpdateDownloadDialog`: İlerleme çubuğu, indirilen boyut, kalan süre ve indirme tamamlandığında otomatik kurulum tetikleme akışı sunar.
4. **Windows Dosya Kilidini Aşma Stratejisi (`src/updater.py`):**
   - **Inno Setup (`.exe`):** İndirilen `Kast-vX.Y.Z-Setup.exe` dosyası `subprocess.Popen([installer_path], creationflags=subprocess.DETACHED_PROCESS)` ile tamamen bağımsız bir süreç olarak başlatılır ve mevcut Kast Studio süreci anında `QApplication.quit()` ile temiz şekilde kapanır. Inno Setup kendi içinde çalışan sürecin kapanmasını bekleyip dosyaları günceller.
   - **Portable (`.zip`):** İndirilen zip dosyası `%TEMP%` klasörüne ayıklanır. Ardından geçici bir Windows toplu iş dosyası (`kast_update.bat`) oluşturulur. Bu betik:
     1. Mevcut Kast Studio sürecinin PID'sinin sonlanmasını bekler (`tasklist /FI "PID eq ..."`).
     2. `robocopy /E /MOVE` komutu ile yeni dosyaları hedef dizine taşır.
     3. Kast Studio uygulamasını yeniden başlatır (`start "" "Kast.exe"`).
     4. Kendini ve geçici dosyaları siler (`del "%~f0"`).
   - Betik `DETACHED_PROCESS` bayrağıyla arka planda çalıştırılarak ana uygulamanın dosya kilidi sıfırlanır.
5. **Kast Studio Ana Arayüz Entegrasyonu (`src/gui.py`):**
   - Başlatma esnasında `QTimer.singleShot(1500, self._auto_check_updates)` ile pencere yüklendikten 1.5 saniye sonra sessiz kontrol çalıştırılır. Güncelleme yoksa veya ağ hatası olursa kullanıcıya hiçbir rahatsız edici mesaj gösterilmez. Yalnızca güncelleme varsa bildirim açılır.
   - Header alanına "🔄 Güncellemeleri Denetle" (`btn_check_updates`) butonu yerleştirilmiştir. Manuel tıklandığında buton durumu değişir, hata varsa uyarı penceresi, sürüm güncelse bilgi penceresi açılır.

## Alternatifler (Alternatives Considered)

- **Alternatif 1: WinSparkle veya PyUpdater Kütüphanesi Kullanımı:**
  - *Değerlendirme:* Hazır C++/Python güncelleme kütüphaneleri.
  - *Reddedilme Gerekçesi:* Ek ikili bağımlılıklar (DLL), C derleyicisi gereksinimi ve imza anahtarı sunucuları gerektirir. Kast'ın sıfır dış bağımlılık prensibini bozar ve taşınabilir Python ortamlarında derleme karmaşıklığını artırır.
- **Alternatif 2: Otomatik Zorunlu Güncelleme (Silent Force Update):**
  - *Değerlendirme:* Kullanıcıya sormadan arka planda indirip zorla yeniden başlatmak.
  - *Reddedilme Gerekçesi:* Stüdyo kayıt ortamlarında kritik anlarda kullanıcının çalışmasını bölme veya kaydedilmemiş senaryo analizini kaybetme riski taşır. Kullanıcı onayı zorunlu tutulmalıdır.
- **Alternatif 3: Yalnızca GitHub Releases Web Sayfasına Link Vermek:**
  - *Değerlendirme:* Güncelleme butonuna basıldığında tarayıcıda `github.com/.../releases` sayfasını açmak.
  - *Reddedilme Gerekçesi:* Son kullanıcıyı tarayıcı açma, doğru asset'i bulma, indirme dizinini seçme ve elle kurma yüküyle baş başa bırakır. Stüdyo kullanıcı deneyimini zayıflatır.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- **Kusursuz Kullanıcı Deneyimi:** Güncelleme denetimi, indirme ve kurulum tamamen uygulama içinden, modern stüdyo temalı diyaloglarla tek tıkla tamamlanır.
- **Sıfır Dış Bağımlılık:** Yalnızca Python standart kütüphaneleri ve PySide6 kullanılmış, paket boyutu ve dağıtım karmaşıklığı artırılmamıştır.
- **Dağıtım Güvenliği:** Setup ve Portable kullanıcıları birbirine karıştırılmadan doğru paketle güncellenir.
- **Kilitlenmesiz Kurulum:** Windows işletim sisteminde `ERROR_ACCESS_DENIED` hatası olmadan arka plan devir-teslim betiğiyle güvenli güncelleme sağlanır.
- **Asenkron Kararlılık:** QThread kullanımı sayesinde ağ gecikmelerinde arayüz asla donmaz.

### Olumsuz / Kısıtlar:
- **Geliştirici Ortamı Kısıtı:** Kaynak koddan (`python kast.py --gui`) çalışan geliştirici ortamlarında güncelleme kurulmaz; kullanıcıya geliştirici modunda olduğu bildirilir.
- **GitHub API Hız Sınırı (Rate Limit):** Kimliksiz (unauthenticated) GitHub API isteklerinde saatlik 60 istek sınırı bulunmaktadır. Ancak Kast Studio yalnızca açılışta ve manuel tıklandığında tek bir GET isteği yaptığı için bu sınır stüdyo kullanımı için fazlasıyla yeterlidir.

## İlgili Sayfalar

- [[github-release-updater]]
- [[qt6-desktop-gui]]
- [[inno-setup-installer]]
- [[pyinstaller-standalone-packaging]]
- [[github-actions-release-workflow]]
- [[adr-005-qt6-windows-studio-gui]]
- [[adr-006-windows-standalone-installer-and-ci]]
- [[index]]
- [[log]]
