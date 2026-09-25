---
title: "ADR-007: Masaüstü GUI Çoklu Dosya Seçimi ve Sıralı Toplu İşleme (Batch Processing) Mimarisi"
type: architecture-decision-record
status: accepted
date: 2026-09-26
domain: architecture-decisions
tags:
  - adr
  - gui
  - batch-processing
  - pyside6
  - libreoffice
  - fault-tolerance
  - studio
---

# ADR-007: Masaüstü GUI Çoklu Dosya Seçimi ve Sıralı Toplu İşleme (Batch Processing) Mimarisi

## Bağlam (Context)

Kast 2.0 senaryo ve dublaj kast tablosu çıkarma sistemi, [[adr-005-qt6-windows-studio-gui]] kararıyla modern bir masaüstü grafik arayüzüne kavuşmuştur. Ancak stüdyo operasyonlarının doğası gereği, çevirmenler ve ses teknisyenleri genellikle tek bir bölümle değil; dizi sezonları (ör. 10-24 bölüm), mini diziler veya çoklu senaryo paketleriyle çalışmaktadır.

Mevcut tekil dosya işleme akışında kullanıcıların her bir bölüm için dosyayı tek tek seçmesi, işlemin bitmesini beklemesi ve sonraki dosyayı tekrar yüklemesi stüdyo iş akışında ciddi bir zaman kaybı ve sürtünme yaratmaktadır. Çoklu dosya desteğinin tasarlanmasında şu kritik operasyonel ve teknik kısıtlar ortaya çıkmıştır:

1. **Ofis Yazılımı ve Profil Kilitlenmeleri (LibreOffice User Profile Locks):**
   - Kast'ın kesin sayfa numarası üretme mimarisi ([[adr-002-strict-pdf-pagination-flow]], [[headless-pdf-converter]]), Word senaryolarını arka planda geçici PDF formatına dönüştürmek için LibreOffice (`soffice`) headless motorunu veya Windows Word COM otomasyonunu kullanır.
   - LibreOffice headless süreci varsayılan olarak kullanıcı profil dizininde bir kilit dosyası (`.lock`) oluşturur. Birden çok `soffice` sürecinin eşzamanlı (paralel) başlatılması durumunda profil kilidi çekişmesi (lock contention), `"Fatal Error: The application cannot be started"` hatası veya süreçlerin birbirini beklemesi sebebiyle kilitlenmeler (deadlock) meydana gelir.
2. **Sistem Kaynaklarının Tükenmesi (CPU/RAM Exhaustion):**
   - Dublaj stüdyolarındaki iş istasyonlarında eşzamanlı olarak ağır dijital ses işleme istasyonları (Pro Tools, Nuendo vb.) çalışmaktadır.
   - Senaryo ayrıştırma, OpenXML DOM manipülasyonu ve PDF metin analizi (`pdfplumber`) yoğun bellek ve işlemci gücü tüketir. Birden fazla dosyanın paralel işlenmesi iş istasyonunu kilitleyebilir ve stüdyo ses oturumlarını tehlikeye atabilir.
3. **Microsoft Word COM İş Parçacığı Çakışmaları:**
   - Windows ortamında Word COM otomasyonu, tekil STA (Single-Threaded Apartment) kuralına tabidir. Paralel iş parçacıklarından Word COM nesnelerine erişilmeye çalışıldığında RPC sunucu meşgul (`RPC_E_SERVERCALL_RETRYLATER`) hataları oluşur.
4. **Dosya Türü Uyumsuzluğu ve Arayüz Belirsizliği:**
   - Word (`.docx`) ve PDF (`.pdf`) dökümanları farklı ayrıştırma motorlarıyla ([[dubbing-docx-parser]], [[dubbing-pdf-parser]]) işlenir.
   - Word senaryolarında orijinal belgenin sonuna tablo ekleme (`in_place`) seçeneği mevcutken, PDF belgelerinde format gereği bu seçenek devre dışıdır. Karma dosya türlerinin aynı anda seçilmesi arayüz durumunda mantıksal tutarsızlıklara yol açar.
5. **Hata İzolasyonu İhtiyacı (Fault Tolerance):**
   - 20 bölümlük bir sezonda 3. bölümdeki bozuk bir XML veya eksik izin sebebiyle tüm toplu işlemin durdurulması (`fail-fast`) kabul edilemez bir kullanıcı deneyimidir. Hata veren dosyanın izole edilmesi, diğer dosyaların işlenmeye devam etmesi ve işlem sonunda şeffaf bir özet sunulması şarttır.

## Karar (Decision)

Kast 2.0 masaüstü arayüzünde çoklu dosya seçimi ve toplu işleme için kaynak güvenliğini, sistem kararlılığını ve kullanıcı konforunu garanti altına alan 5 temel mimari ilke kabul edilmiştir:

1. **Azami 25 Dosya Sınırı (`MAX_FILES = 25`):**
   - Tek bir işlemde işlenebilecek azami dosya adedi 25 olarak sınırlandırılmıştır.
   - Bu sınır, tipik bir televizyon/dijital platform dizi sezonu bölüm hacmini (genellikle 8-24 bölüm) tam olarak karşılar. Bellek sızıntılarını, aşırı dosya tanıtıcı (file descriptor) kullanımını ve arayüz kuyruk karmaşasını engeller.
2. **Homojen Dosya Türü Kuralı (Uniform Extension Rule):**
   - Seçilen dosyaların tamamının ya `.docx` ya da tamamının `.pdf` olması zorunlu kılınmıştır.
   - `.docx` ve `.pdf` dosyalarının karma biçimde seçilmesi durumunda `DropZoneWidget` seçimi anında reddeder ve `validation_error` sinyaliyle açıklayıcı bir uyarı gösterir.
   - Bu sayede çıktı seçeneklerinin (`standalone` vs `in_place`) doğruluğu ve motor parametreleri garantiye alınır.
3. **Sıralı Toplu İşleme (Sequential Batch Execution, Concurrency = 1):**
   - Arka plan iş parçacığı olarak `BatchExtractionWorker(QThread)` mimarisi uygulanmıştır.
   - Seçilen dosyalar paralel iş parçacıklarına dağıtılmak yerine tek bir arka plan thread'i üzerinde kesinlikle **sıralı (sequential, concurrency limit = 1)** olarak işlenir.
   - Böylece LibreOffice profil kilidi çakışmaları, Word COM RPC hataları ve CPU aşırı yüklenmesi sıfıra indirilmiştir.
4. **Dosya Bazında Hata Toleransı ve İzolasyonu (Per-File Fault Tolerance):**
   - Her bir dosya bağımsız `try...except` bloğuyla işlenir.
   - Bir dosyada meydana gelen hata (`PermissionError`, `ValueError`, bozuk dosya formatı vb.) yakalanır, `file_error` sinyaliyle günlüğe yazılır ve durum özetine `status: error` olarak işlenir.
   - Hata oluşan dosya diğer dosyaların yürütülmesini engellemez; döngü sonraki dosyaya güvenle geçer.
   - Tüm işlem tamamlandığında `all_finished` sinyaliyle her dosyanın başarı durumunu, çıktı yolunu ve hata mesajını içeren kapsamlı bir özet (`list[dict]`) ana pencereye iletilir.
5. **Dinamik Mizanpaj ve Stüdyo Sonuç Kartı (`result_card`):**
   - Arayüz durumuna göre 3 farklı sonuç paneli dinamik olarak render edilir:
     - **Tam Başarı (0 Hata):** Yeşil başarı rozeti, toplam karakter sayısı, toplam replik adedi ve oluşturulan dosya oranı.
     - **Kısmi Hata (Bazı dosyalar başarılı, bazıları hatalı):** Kehribar sarısı uyarı rozeti, başarılı ve hatalı dosya sayıları.
     - **Tam Başarısızlık (Tüm dosyalar hatalı):** Kırmızı hata rozeti.
   - Çoklu dosya tamamlandığında buton metni dinamik olarak `"📄 Son Dosyayı Aç"` olarak güncellenir; tekli dosyalarda geriye dönük uyumlu `"📄 Dosyayı Aç"` korunur.

## Alternatifler (Alternatives Considered)

- **Alternatif 1: Çok İş Parçacıklı Paralel İşleme (`QThreadPool` / `ProcessPoolExecutor`):**
  - *Değerlendirme:* Çok çekirdekli modern işlemcilerde tüm dosyaları eşzamanlı çalıştırmak teorik olarak toplam süreyi kısaltabilir.
  - *Reddedilme Gerekçesi:* LibreOffice headless çalışma zamanı aynı kullanıcı kurulum dizininde birden fazla paralel süreç başlatıldığında kilitlenir (`Fatal Error: The application cannot be started`). Windows Word COM ise STA iş parçacığı modelinde RPC meşgul hataları fırlatır. Ayrıca stüdyo DAW iş istasyonlarında CPU'nun %100'e fırlaması ses kayıt ve miksaj süreçlerini kesintiye uğratır.
- **Alternatif 2: Sınırsız Dosya Seçimi (No Upper Limit):**
  - *Değerlendirme:* Kullanıcının istediği kadar (50-100+) dosya seçmesine izin verilmesi.
  - *Reddedilme Gerekçesi:* Çok yüksek dosya adetlerinde LibreOffice dönüştürme döngüsü saatler sürebilir, geçici disk alanı dolabilir ve bellek tüketimi kontrolsüz artabilir. 25 dosya sınırı stüdyo iş akışlarındaki sezonluk paketlerle tam örtüşür.
- **Alternatif 3: Karma Dosya Türlerine İzin Verme (.docx ve .pdf karışık):**
  - *Değerlendirme:* Kullanıcının aynı anda hem Word hem PDF dosyalarını sürükleyebilmesi.
  - *Reddedilme Gerekçesi:* PDF dosyalarında orijinal dökümanın sonuna ekleme (`in_place`) teknik olarak imkansızken Word dosyalarında desteklenir. Karma yapıda radyo butonlarının davranışı belirsizleşir ve kullanıcı arayüzü mantıksal tutarsızlığa düşer.
- **Alternatif 4: Hata Anında İşlemi Durdurma (Fail-Fast):**
  - *Değerlendirme:* İlk hatada döngüyü kesip kullanıcıya hata mesajı vermek.
  - *Reddedilme Gerekçesi:* Örneğin 20 dosyalık bir pakette 18. dosya hatalıysa, ilk 17 dosyanın işlenmiş emeği boşa gitmemeli, 19 ve 20. dosyalar da tamamlanmalıdır. Kullanıcıya hangi dosyaların üretildiği, hangilerinde problem çıktığı şeffaf bir özet kartıyla sunulmalıdır.

## Sonuçlar ve Etkiler (Consequences)

### Olumlu:
- **Kaynak Güvenliği ve Kararlılık:** Concurrency = 1 sıralı mimari sayesinde LibreOffice profil kilitlenmeleri, Word COM çakışmaları ve arayüz donmaları tamamen engellenmiştir.
- **Yüksek Hata Toleransı:** Birkaç dosyadaki biçim bozuklukları veya erişim engelleri tüm sezonluk işleme sürecini aksatmaz.
- **Gelişmiş Stüdyo Ergonomisi:** Çevirmenler tüm bir sezonu tek bir sürükle-bırak hamlesiyle arka plana devredebilir.
- **Geriye Dönük Tam Uyumluluk:** Tekil dosya işleme akışı bozulmamış; `ExtractionWorker` sınıfı `BatchExtractionWorker` üzerinden türetilerek mevcut kod ve testlerle %100 uyumlu tutulmuştur.
- **Net İlerleme Matematiği:** Genel ilerleme çubuğu toplam dosya dilimleri üzerinden hesaplanarak kullanıcıya pürüzsüz ve gerçekçi bir durum bildirimi sağlar.

### Olumsuz / Kısıtlar:
- **Sıralı İşlem Süresi:** Paralel yürütmeye kıyasla toplam işlem süresi dosya sayısıyla doğrusal (linear) artar; ancak stüdyo ortamı kararlılığı ve kilitlenme riskinin sıfırlanması hızdan öncelikli kabul edilmiştir.

## İlgili Sayfalar

- [[qt6-desktop-gui]]
- [[dubbing-docx-parser]]
- [[dubbing-pdf-parser]]
- [[headless-pdf-converter]]
- [[cast-extraction-result]]
- [[adr-005-qt6-windows-studio-gui]]
- [[adr-002-strict-pdf-pagination-flow]]
