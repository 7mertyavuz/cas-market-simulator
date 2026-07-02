# Devam Promptu — `microstructure-analyzer`

> Bu prompt'u microstructure-analyzer reposunda çalışan AI kodlama asistanına ver. Amaç: repo'yu hibrit CAS planına uyumlu hale getirmek; kendi işlevini bozmadan `cas-market-simulator`'a iki yeni arayüz açmak.

## Bağlam — bu repo'nun hibrit sistemdeki iki rolü
1. **Katman 1 (analist çekirdeği) — akış sensörü:** Yeni indikatör+formasyon motoruna `FlowState` besler (on-chain emir akışı boyutu).
2. **Katman 2 (CAS simülasyonu) — ajan + çevre:** Whale/MEV/Retail aktör modeli, simülatördeki **ajan sınıflarının davranış şablonu**; simülasyon modundaki sentetik akış üreteci ise **Environment'in emir-akışı boyutu** olur.

Bu repo zaten 5 katmanlı, olgun ve saf Python+NumPy (sklearn/torch yok), simülasyon modu mevcut. Mimariyi koru, üstüne ekle.

## Görev 1 — `FlowFeed` adaptörü (Katman 1 köprüsü)
`src/api/flow_feed.py` (yeni) içinde, `00-ORTAK-SOZLESME.md`'deki `FlowState`'i üreten temiz bir sınıf yaz:

```python
class FlowFeed:
    def __init__(self, mode="simulation"): ...   # "simulation" | "live"
    def latest(self, token: str) -> FlowState: ...
```

- `flow_imbalance`, `vpin_toxicity`, `whale_net_usd`, `actor_mix`, `direction_prob_up`, `lead_lag_spread`, `regime` alanlarını mevcut `src/features/*` ve `src/predict/*` çıktısından doldur.
- `print`'e değil, struct'a yaz. Mevcut `main.py` döngüsü bu sınıfı kullanacak şekilde refactor edilebilir ama davranışı aynı kalmalı.
- Hem simülasyon hem canlı modda çalışmalı (WSS_URL yoksa simülasyon).

## Görev 2 — Ajan davranış şablonu dışa aktarımı (Katman 2 için)
Simülatör, aktör tiplerini sentetik ajan olarak kullanacak. `src/actor/agent_profiles.py` (yeni) içinde her aktör için **parametrik davranış tanımı** ver (kod değil veri): tipik emir boyutu dağılımı, gas/agresiflik, frekans, tetikleyici koşul.

```python
WHALE   = AgentProfile(size_usd=(50_000, 5_000_000), freq="low",  aggression=0.3, trigger="onchain_flow")
MEV_BOT = AgentProfile(size_usd=(1_000, 200_000),    freq="high", aggression=1.0, trigger="victim_in_mempool")
RETAIL  = AgentProfile(size_usd=(50, 5_000),         freq="mid",  aggression=0.5, trigger="sentiment|momentum")
```

Ayrıca mevcut `src/mev/*` (sandwich/jit/arbitrage/builder_tip) mantığını, simülatörde **MEV ajanının karar fonksiyonu** olarak çağrılabilir saf fonksiyonlar hâline getir (yan etkisiz, test edilebilir).

## Görev 3 — Çevre üreteci olarak simülasyon modu
Mevcut simülasyon akış üretecini (`mempool_listener` sim modu) `cas-market-simulator`'ın `Environment` katmanından **enjekte edilebilir** yap: dışarıdan verilen ajan emirlerini kabul eden, geri-bildirim döngüsü kurulabilen bir arayüz ekle. Yani simülatör "şu ajan şu emri verdi" diyebilmeli ve akış metrikleri buna tepki vermeli.

## Kısıtlar ve dikkat
- **EVM önce, SUI sonra.** Decode katmanı Ethereum'a kurulu. SUI (object-centric tx modeli) ayrı bir epik; şimdi üstlenme.
- **Çift sayım uyarısı:** `FlowState` sinyali, yeni indikatör motorunun `order_flow`/`onchain_flow` faktörüyle örtüşebilir. Bunu motor tarafı düşük ağırlıkla ekleyecek; sen sadece ham/temiz metriği ver, ağırlık kararı verme.
- Mevcut 11 test dosyası geçmeye devam etmeli; yeni kod için yeni testler ekle.
- Saf Python+NumPy kuralını koru.

## Tanım: bitti sayılır
- [ ] `FlowFeed.latest(token)` simülasyon ve canlı modda geçerli `FlowState` döndürüyor.
- [ ] `agent_profiles.py` üç aktör için parametrik profil veriyor; MEV mantığı saf fonksiyon olarak çağrılabiliyor.
- [ ] Simülasyon modu dışarıdan ajan emri kabul edebiliyor (enjekte edilebilir çevre).
- [ ] Yeni testler + mevcut testler yeşil.
- [ ] README'ye "cas-market-simulator entegrasyonu" bölümü eklendi.
