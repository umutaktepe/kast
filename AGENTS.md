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
     - `core-models/`: Temel veri şemaları, modeller ve veri sözleşmeleri.
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
- Yeni bir kütüphane eklendiğinde veya çıkarıldığında (Örn: `dxpdf` çıkarılıp `LibreOffice` eklenmesi).
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

## 5. Geliştirici Ajanın TypeSafe AI (System One) Karar ve Doğrulama Protokolü

`/typesafe-ai` skill'i, Kast masaüstü uygulamasının içine gömülü çalışan bir runtime kodu **değildir**. Kod tabanında görev alan **yapay zeka ajanının (AI Coding Agent / Antigravity)**; mimari kararlarında, alternatif seçimlerinde, risk değerlendirmelerinde, kod incelemelerinde ve wiki sağlığı denetimlerinde nesnel, tip güvenli ve kalibre edilmiş kararlar almasını sağlayan bir **mühendislik karar destek primitifidir**.

Ajanlar, karmaşık veya belirsiz durumlarda serbest metinli sübjektif varsayımlarda bulunmak yerine `/typesafe-ai` skill'ini ve System One primitiflerini (`Choice`, `Score`, `Noul`) şu senaryolarda doğrudan devreye sokmalıdır:

1. **Mimari Alternatif ve Tasarım Seçimi (ADR & Planning):**
   - Bir özellik veya refactor için 2 veya daha fazla teknik yaklaşım (örn. process isolation vs threading, kuyruk stratejileri, veri modelleri) değerlendirilirken, ajanın seçimini nesnel kriterlerle doğrulaması için `Choice` primitifi kullanılır.
2. **Regresyon ve Kırılma Riski Puanlama (Risk Assessment):**
   - Çekirdek modüllerde (sayfalama motoru, OpenXML ayrıştırma, arka plan worker'ları, kurulum ve derleme betikleri) değişiklik yapmadan önce değişikliğin sistem kararlılığına getirdiği risk seviyesi `Score` (düşük, orta, yüksek, kritik) ile ölçülür. Yüksek veya kritik risk durumlarında ajan ilave savunma testleri (regression test fixtures) inşa eder.
3. **Living Architecture ve Kural Çelişki Denetimi (Contradiction Check):**
   - Yapılan bir kod değişikliğinin veya yeni açılan bir wiki sayfasının var olan ADR'lerle, modellerle veya `AGENTS.md` kurallarıyla anlamsal bir çelişki üretip üretmediği `Noul` (Yes/No) ile doğrulanır.
4. **Karmaşık Hata ve Uç Vaka Sınıflandırması (Root Cause Triage):**
   - Testlerde veya işletim sistemi çağrılarında (Word COM kilidi, LibreOffice profil çakışması, GUI deadlock vb.) beklenmeyen bir hata oluştuğunda olası kök neden hipotezleri `Choice` ile elenir ve önceliklendirilir.
5. **Skill Çağrısı, Sandbox ve Çalıştırma Yöntemi:**
   - Ajan, `/home/umutaktepe/.gemini/config/skills/typesafe-ai/SKILL.md` yönergelerini takip ederek `typesafe-ai/scripts/typesafe_api.py` betiğini terminalden CLI veya Python üzerinden çağırır (`call_system_one`).
   - **Sandbox Bypass Zorunluluğu:** `api.typesafe.ai` uç noktası harici ağ erişimi gerektirdiğinden, standart sandbox ortamı bu HTTP çağrısını engeller (`HTTP 403 / Request not allowed by policy`). Bu nedenle TypeSafe API çağrısı içeren komutlar çalıştırılırken `run_command` aracında mutlaka `BypassSandbox: true` parametresi kullanılmalıdır.
   - Sorular atomik tanımlanmalı, bağlam (`state`) açıkça aktarılmalıdır.
6. **Ortam ve Fallback Bağımsızlığı:**
   - Ortamda `TYPESAFE_API_KEY` bulunmadığı veya ağ bağlantısı olmadığı durumlarda ajan bloklanmaz; doğrudan kendi deterministik mantığı ve testleriyle karar sürecini sürdürür.
