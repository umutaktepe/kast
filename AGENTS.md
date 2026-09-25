# AGENTS.md — Kast 2.0 Living Architecture / LLM Wiki Kural Seti

> Bu belge, Kast kod tabanında görev alacak tüm yapay zeka ajanları (AI Coding Agents / LLMs) için bağlayıcı ve zorunlu bir operasyonel kural setidir.
> Proje, Andrej Karpathy'nin **"LLM Wiki / Living Architecture"** paradigmasıyla yönetilmektedir.

---

## 1. Temel Mimari Prensipler ve Yasaklar

1. **Sayısal/Kitap Düzeni Yasağı:**
   - Asla `"01-giris"`, `"02-moduller"`, `"bolum-1"` gibi sıralı kitap veya kılavuz yapıları oluşturulamaz.
   - Mimari, basılı bir kılavuz değil; yaşayan, ilişkisel ve graf tabanlı bir mühendislik wikisidir.
2. **Fonksiyonel Domain Ayrımı:**
   - Tüm yeni sayfalar, ilgili fonksiyonel domain klasörü altına yerleştirilmelidir (`docs/kast-app-wiki/`):
     - `architecture-decisions/`: Mimari Karar Kayıtları (ADR'ler).
     - `core-models/`: Temel veri şemaları, modeller ve TypeSafe soru sözleşmeleri.
     - `parsing-engine/`: Metin işleme, başlık filtreleme, zaman kodu tespiti ve anlamsal kararlar.
     - `pagination-subsystem/`: Sayfalama, PDF dönüştürücü ve mizanpaj motorları.
     - `document-generation/`: Word tablo yazma ve tipografi motoru.
     - `interfaces-and-runtime/`: CLI, TUI ve kurulum/dağıtım betikleri.
   - Yeni bir domain ihtiyacı doğduğunda rastgele klasör açılmamalı; mimari role uygun yeni bir fonksiyonel domain tanımlanmalıdır.
3. **Graf Hijyeni (Cluster Topolojisi):**
   - Her sayfanın her sayfaya rastgele bağlandığı anlamsız düğüm yumaklarından (hairballs) kaçınılmalıdır.
   - Sayfalar yalnızca doğrudan bağımlı olduğu mimari karara ([[adr-...]]), veri modeline veya çekirdek modüle bağlanmalıdır.
4. **Obsidian Uyumlu Wikilink Sözdizimi:**
   - Standart Markdown linkleri `[metin](dosya.md)` wiki içi bağlantılarda KESİNLİKLE KULLANILMAZ.
   - Bağlantılar her zaman `[[kebab-case-sayfa-adi]]` biçiminde, yol veya `.md` uzantısı olmadan verilmelidir.
5. **İsimlendirme Standardı (Kebab-case):**
   - Tüm klasörler ve dosyalar istisnasız küçük harf ve tireli (`kebab-case.md`) olmalıdır.

---

## 2. Mimari Değişiklik ve ADR Zorunluluğu

Kod tabanında kritik bir tasarım veya mimari değişiklik yapılmadan önce mutlaka bir ADR yazılmalıdır:
- Yeni bir kütüphane eklendiğinde veya çıkarıldığında (Örn: `dxpdf` çıkarılıp `LibreOffice` eklenmesi veya TypeSafe AI entegrasyonu).
- Veri modellerinin sözleşmesi (schema) değiştiğinde.
- Giriş/Çıkış veya sayfalama stratejisi revize edildiğinde.

Format: `docs/kast-app-wiki/architecture-decisions/adr-00x-[konu].md`
Zorunlu Bölümler:
1. **Bağlam (Context):** Kararın alınmasını gerektiren sorun veya ihtiyaç.
2. **Karar (Decision):** Seçilen mimari ve teknik yöntem.
3. **Alternatifler (Alternatives Considered):** Değerlendirilen ve elenen diğer yaklaşımlar (neden elendikleriyle birlikte).
4. **Sonuçlar ve Etkiler (Consequences):** Olumlu getiriler ve kabullenilen ödünleşimler (trade-offs).
5. **İlgili Sayfalar:** Bağlantılı `[[wikilink]]` listesi.

---

## 3. Kod Değişikliklerinde Wiki Güncelleme Protokolü

Herhangi bir ajan kod tabanında bir değişiklik yaptığında şu döngüyü işletmekle yükümlüdür:

1. **İlgili Atomik Sayfayı Güncelle:** Kodda bir fonksiyon, sınıf veya davranış değiştiyse ilgili `[[sayfa]]` dosyasını güncelle.
2. **Gerekiyorsa Yeni Sayfa Aç:** Yeni bir modül veya model eklendiyse uygun domain altında atomik sayfasını oluştur.
3. **Fihristi Güncelle (`index.md`):** `docs/kast-app-wiki/index.md` dosyasına yeni sayfanın wikilinkini ve tek satırlık özetini ekle.
4. **Günlüğe İşle (`log.md`):** `docs/kast-app-wiki/log.md` dosyasına kronolojik kayıt düş:
   ```markdown
   ## [YYYY-MM-DD] [eylem-türü] | Başlık veya Değişiklik Özeti
   - **Ajan Rolü:** ...
   - **Yapılan İşlem:** ...
   - **Etkilenen Sayfalar:** [[sayfa-1]], [[sayfa-2]]
   ```

---

## 4. Wiki Sağlık Denetimi (Wiki Linting)

Periyodik olarak ajanlar şu kontrolleri yapmalıdır:
- **Yetim Sayfa (Orphan):** Hiçbir sayfadan link almayan sayfa kalmamalıdır.
- **Kırık Link (Broken Wikilink):** `[[hedef]]` linkinin karşılığı olan bir `.md` dosyası mutlaka mevcut olmalıdır.
- **Çelişkili İddialar (Contradictions):** Yeni eklenen özelliklerin eski belgelenmiş davranışlarla çelişmediği teyit edilmelidir.

---

## 5. TypeSafe AI (System One) Kullanım ve Karar Protokolü

Kast kod tabanında anlamsal metin ayrıştırma, künye/karakter filtreleme ve sınıflandırma gerektiren durumlarda TypeSafe AI (`/typesafe-ai`) yetenekleri kullanılırken şu kurallara uyulmalıdır:

1. **Skill Çağrısı ve Rol Ayrımı:**
   - Ajanlar, karmaşık regex veya kırılgan string kontrollerinin yetersiz kaldığı anlamsal ayrıştırma durumlarında serbest metin üreten LLM çağrıları (`prompt-and-parse`) yerine `/typesafe-ai` skill'ini ve System One primitiflerini (`Choice`, `Score`, `Noul`) devreye sokmalıdır.
2. **Merkezi Tanım İlkesi (Centralized Judgments):**
   - Soru şablonları (`questions`), değerlendirme rubrikleri (`criteria`) ve olasılık/güven eşikleri (`thresholds`), kod bloklarının arasına dağıtılamaz.
   - İnsan denetimini ve kod incelemesini kolaylaştırmak amacıyla tüm TypeSafe soru ve kriterleri tek bir merkezi modülde (örneğin `src/typesafe_judgments.py`) toplanmalıdır.
3. **Atomik Değerlendirme & Kodda Birleştirme:**
   - Çok boyutlu kararlar tek bir karmaşık soruya yüklenmemelidir. Sorular atomik parçalara bölünmeli, tek bir `state` üzerinden paralel sorgulanmalı ve nihai karar kural/ağırlık mantığı ile Python kodunda birleştirilmelidir.
4. **Çevrimdışı ve Sıfır Bozulma (Offline Fallback):**
   - Kast'ın temel çalışma felsefesi yerel ve hızlı olmaktır. API anahtarı (`TYPESAFE_API_KEY`) bulunmadığında veya ağ kesintisi/istek hatası durumunda sistem kesinlikle çökmeyecek; zarifçe mevcut kural tabanlı OpenXML motoruna (`metadata-filtering`, kural tabanlı parser) geri çekilecektir (fallback).
5. **Ortam Değişkeni Güvenliği:**
   - `TYPESAFE_API_KEY` kesinlikle dosyalara veya test fixture'larına hardcode edilemez; yalnızca ortam değişkeninden okunmalıdır.
