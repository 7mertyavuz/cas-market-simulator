# Devam Promptu — `macro-sentiment-agent`

> Bu prompt'u macro-sentiment-agent reposunda çalışan AI kodlama asistanına ver. Amaç: repo'yu hibrit CAS planına bağlamak; mevcut Faz 0–5 boru hattını bozmadan iki yeni arayüz açmak ve planlı Faz 6'yı bu yöne kanalize etmek.

## Bağlam — bu repo'nun hibrit sistemdeki iki rolü
1. **Katman 1 (analist çekirdeği) — sentiment sensörü:** Yeni indikatör+formasyon motoruna `SentimentState` besler (anlatı/makro boyutu, bir faktör olarak).
2. **Katman 2 (CAS simülasyonu) — dışsal şok enjektörü:** panic/euphoria/fed_tone/narrative_shift olaylarını `ShockEvent` olarak üretip simülasyondaki çevreye **dış şok** olarak sokar; ajanların tepkisini ve kaskadı gözlemek için.

Repo zaten olay-güdümlü, Protocol-tabanlı, temiz. Faz 0–5 bitti. Bu yapı korunacak.

## Görev 1 — `SentimentFeed` adaptörü (Katman 1 köprüsü)
`src/macro_sentiment/api/sentiment_feed.py` (yeni) içinde, `00-ORTAK-SOZLESME.md`'deki `SentimentState`'i üreten sınıf:

```python
class SentimentFeed:
    def __init__(self, mode="offline"): ...   # "offline" (sözlük/replay) | "live"
    def latest(self, entity: str) -> SentimentState: ...
    def shocks(self, since: datetime) -> list[ShockEvent]: ...
```

- `polarity`, `intensity`, `emotion{fear,greed,uncertainty}`, `confidence`, `fed_tone`, `source_breakdown` alanlarını mevcut `signals/` + `nlp/` çıktısından doldur.
- `fed_tone`: hawkish/dovish ekseni zaten LLM yolunda var; yoksa `None`.

## Görev 2 — `ShockEvent` akışı (Katman 2 için — en kritik yeni yetenek)
Mevcut sinyaller (panic/euphoria/fed_tone) zaten ayrık olaylar. Bunları simülasyona enjekte edilebilir şok olaylarına çevir:
- `kind`, `entity`, `magnitude` (0..1, sinyal şiddetinden), `decay_halflife_s` (örn. panik 30 dk, fed_tone saatler), `ts`.
- `shocks(since)` bu olayları zaman sırasıyla döndürür.

## Görev 3 — Deterministik replay / senaryo modu (simülasyon için)
Simülatörün tekrarlanabilir deney yapabilmesi için **scriptli haber zaman çizelgesi** desteği ekle: JSONL bir senaryo dosyası (`t=0: fed hawkish; t=300s: panik haberi; ...`) verildiğinde, `SentimentFeed`/`shocks` bunu deterministik olarak oynatsın. Bu, mevcut `backtest` harness'inin yanına oturur ve onunla format paylaşabilir.

## Görev 4 — Faz 6'yı bu yöne kanalize et
Planlı Faz 6 (canlı çoklu kaynak: Fed/sosyal canlı, TimescaleDB, HITL) devam edebilir; ama önceliklendirme: önce offline/replay yolu sağlam olsun (simülatör buna bağımlı), canlı kaynaklar sonra.

## Kısıtlar ve dikkat
- **Maliyet kontrolü:** Hibrit NLP router'ı (rutin→FinBERT, yüksek-etki→LLM) koru. Simülasyon/replay modu hiçbir API çağırmamalı.
- **Çift sayım:** `SentimentState`, yeni motorun "Haber" faktörüyle örtüşür. Ham/temiz sentiment'i ver; ağırlık kararını motora bırak.
- Mevcut 15 test geçmeye devam etmeli; yeni arayüzler için test ekle.
- Konum: "yatırım tavsiyesi değildir" korunur.

## Tanım: bitti sayılır
- [ ] `SentimentFeed.latest(entity)` offline ve live modda geçerli `SentimentState` döndürüyor.
- [ ] `shocks(since)` magnitude + decay'li `ShockEvent` listesi döndürüyor.
- [ ] JSONL senaryo dosyasından deterministik replay çalışıyor (API çağrısı yok).
- [ ] Yeni + mevcut testler yeşil.
- [ ] README'ye "cas-market-simulator entegrasyonu" + senaryo formatı eklendi.
