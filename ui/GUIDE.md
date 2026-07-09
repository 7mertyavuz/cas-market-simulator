# CAS Market Dashboard — Kullanım Kılavuzu

## 1. Dashboard nedir?

CAS Market Dashboard, karmaşık uyarlanabilir sistem (CAS) bakış açısıyla piyasayı gözlemlemeni sağlayan bir analiz ekranıdır. Makro sentiment, mikroyapı (order flow & order book) ve teknik faktörleri tek bir "Analyst Card" üzerinde birleştirir.

> **Amaç otomatik işlem sinyali üretmek değil**, piyasanın yapısını daha hızlı anlamana yardım etmektir.

## 2. Sembol arama

- Üstteki arama çubuğuna istediğin hisse, coin veya para birimi sembolünü yaz.
- **Analiz Et** butonuna bas.
- Hızlı seçim çiplerinden (BTC, ETH, SOL, vb.) de geçiş yapabilirsin.
- Tüm paneller otomatik olarak o sembol için güncellenir.

## 3. Ekranlar ve gösterdikleri

### 3.1 Analist Kartı

Seçtiğin sembol için üretilen ana görüşü gösterir:

| Alan | Açıklama |
|------|----------|
| **Yön** | LONG / SHORT / NEUTRAL tahmini |
| **Confidence** | Modelin faktörler arasında ne kadar uzlaştığı (0-100%) |
| **Faktör Oyları** | Her faktörün (trend, momentum, hacim, orderbook, sentiment) oy ve ağırlığı |
| **Formasyonlar** | Tespit edilen teknik formasyonlar ve güçleri |
| **Risk Parametreleri** | Önerilen stop, take ve pozisyon büyüklüğü (varsa) |

### 3.2 Mikroyapı

| Alan | Açıklama |
|------|----------|
| **Flow Imbalance** | Alım/satış emir akışı dengesizliği |
| **VPIN** | Toksisite / bilgi asimetrisi göstergesi |
| **Whale Net** | Büyük oyuncuların net USD akışı |
| **Actor Mix** | WHALE, MEV_BOT, RETAIL gibi katılımcı oranları |
| **Book State** | Spread, microprice, depth imbalance, OFI, book slope, Kyle λ, iceberg/spoof şüphe skorları |

### 3.3 Sentiment & Şoklar

| Alan | Açıklama |
|------|----------|
| **Polarity** | Metin tabanlı genel duygu (-1 ile +1) |
| **Intensity** | Duygu şiddeti |
| **Confidence** | Sentiment modelinin güveni |
| **Emotion** | Korku, açgözlülük, belirsizlik dağılımı |
| **Fed Tone** | Varsa Fed metinlerinin şahin/güvercin tonu |
| **Aktif Şoklar** | Panik, öfori, Fed tonu değişimi, anlatı kayması gibi ani olaylar |

### 3.4 CAS Laboratuvarı

Simülasyon ortamında fiyat hareketini ve "crowd emergence" skorunu gösterir. Panik şoku ve balina emri butonları ileride simülasyona dışsal etki enjekte edecek; şu an gösterim amaçlıdır.

### 3.5 HITL Onay (Human-in-the-Loop)

Model çıktısını operatör olarak gözden geçirmeni sağlar:

1. **Son Kartı Yükle** ile analyst card'ı getir.
2. İstersen **Override** yönü seç (LONG / SHORT / NEUTRAL).
3. Pozisyon büyüklüğünü slider ile ayarla.
4. Operatör notunu yaz.
5. **Kararı Onayla & Gönder** ile (mock) kaydet.

## 4. Sık kullanılan kısayollar

| İşlem | Yol |
|-------|-----|
| Sembol değiştir | Arama çubuğu veya hızlı çipler |
| Panele geç | Sol sidebar |
| Kılavuzu aç | Sidebar → Kılavuz |

## 5. Önemli uyarı

> Burada gösterilen hiçbir içerik yatırım tavsiyesi değildir. Modeller simülasyon ve/veya sınırlı veriyle çalışır; gerçek sermaye ile işlem yapmadan önce kendi araştırmanı ve risk yönetimini uygula.
