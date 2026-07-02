# Ekleyebileceğin Yeni Agent / Bileşen Önerileri

> İki tür "agent" karışıyor — ayıralım:
> - **(A) Analist sensör/bileşen agent'ları:** Gerçek dünyadan veri okuyup analiz çekirdeğine sinyal besleyen bağımsız repolar (macro-sentiment, microstructure gibi).
> - **(B) CAS simülasyon ajanları:** Simülatörün içinde yaşayan, basit kurallı sentetik botlar; emergence bunların etkileşiminden doğar.

---

## A) Yeni sensör/bileşen agent'ları (analist çekirdeğini zenginleştirir)

| Öneri | Ne yapar | Neden değerli | Öncelik |
|---|---|---|---|
| **derivatives-agent** | Funding, open interest, basis/contango, opsiyon IV (DVOL), put/call | Kriptoda yönün en güçlü erken sinyali türevlerde; likidasyon kaskadlarının yakıtı | Yüksek |
| **liquidity/orderbook-agent** | CEX emir defteri derinliği, spread, likidasyon haritası, kitap dengesizliği | microstructure DEX tarafını tamamlar; CEX mikroyapısı | Yüksek |
| **onchain-fundamental-agent** | Borsa netflow, stablecoin arzı (kuru barut), aktif adres, NVT, ETF akışı | Orta-vade arz/talep ve likidite rejimi; sentiment'ten bağımsız | Orta |
| **intermarket/macro-agent** | DXY, altın, 10Y faiz, S&P korelasyonu, risk-on/off rejimi | Kripto tek başına hareket etmez; makro bağlam güven çarpanı | Orta |
| **cross-exchange-arb-agent** | Borsalar arası fiyat farkı, coinbase premium, lead-lag | Hem sinyal hem simülasyonda arbitraj ajanının gerçek-veri karşılığı | Orta |
| **risk/portfolio-agent** | HRP dağıtım, korelasyon limiti, CVaR/EVT, günlük risk bütçesi | Tek sembolden portföye geçiş; çoklu pozisyonun bütçesi | Orta |
| **execution-agent (paper)** | Sinyali paper emre çevir, slipaj/maliyet modeli, journal forward-test | Doğrulama omurgası — "sinyalin gerçek kenarı var mı" | Yüksek |

> Not: Bunların birçoğunun mantığı KatanaFlow'da hâlihazırda var (`derivs`, `liq_heatmap`, `onchain_flow`, `stablecoin_regime`, `etf_flows`, `hrp`, `paper_trader`, `journal`). Yeni indikatör motorunu sıfırdan yazarken bunları **ayrı sensör agent'ları** olarak bölmek, KatanaFlow'un tek-dosya-yığınından daha temiz olur. Sıfırdan yazma; oradaki saf mantığı modüler agent'lara taşı.

---

## B) Yeni CAS simülasyon ajanları (emergence için — basit tut!)

Simülatördeki popülasyonu zenginleştiren ajan tipleri. **Her biri ~50 satır, tek kural.** Emergence, zengin ajanlardan değil, basit ajanların *etkileşiminden* doğar.

| Ajan | Tek kuralı | Hangi emergence'i besler |
|---|---|---|
| **Momentum/trend takipçisi** | Fiyat yükseliyorsa al | Ralli/balon, pozitif geri-besleme |
| **Ortalama-dönüşçü** | Aşırı sapmada ters pozisyon | İstikrar / fiyat geri çekme |
| **Market-maker** | Spread koy; envanter risk artınca çekil | Likidite kuruması → flash crash tetiği |
| **Panikçi/retail** | Sentiment şoku + düşüşte geç sat | Kaskad, kapitülasyon dibi |
| **Balina** | Seyrek, büyük, fiyatı iten emir | Ani kaymalar, stop avı |
| **MEV/searcher** | Mempool'da kurban gör → sandwich | Mikro-yapı bozulması, retail aleyhine sürtünme |
| **Likidasyon-motoru** | Kaldıraçlı pozisyon eşiği kırılınca zorunlu sat | Likidasyon zinciri → flash crash kaskadı |
| **Arbitrajcı** | İki borsa/varlık farkını kapat | Fiyat yakınsaması, lead-lag transferi |
| **Trend-kırıcı / kontra fon** | Aşırı kalabalıklaşmada ters | Tepe oluşumu, ralli sonu |
| **Haber-tepkicisi** | `ShockEvent` gelince yön al | Dışsal şokun içselleşmesi, aşırı tepki |

### Üst-seviye (meta) ajanlar — opsiyonel, Faz 4
- **Adaptif ajan:** Zarar edince stratejisini mutasyona uğratır (senin metnindeki "evrim"). Basit GA/parametre perturbasyonu.
- **Rejim-değiştiren ajan:** Volatilite rejimine göre momentum↔MR arası geçiş yapar.
- **Sürü/kopyalayıcı ajan:** En kârlı ajanı taklit eder → sürü davranışı, balon büyütme.

---

## Tavsiye — ne zaman ne ekle
1. **Önce derinlik, sonra genişlik.** Faz 1–2'de 3 sensör (yeni indikatör motoru + microstructure + macro) ve 3 sim ajanı (momentum + market-maker + panikçi) yeterli. Önce uçtan-uca çalışsın.
2. **Likidasyon-motoru ajanını erken ekle.** Flash crash emergence'ini en net üreten ajan budur; CAS hikâyenin yıldızı.
3. **execution/journal agent'ı atlama.** Sensör ne kadar çoğalırsa çoğalsın, forward-test omurgası olmadan hepsi gürültü.
4. **Her yeni ajan bir hipotez.** "Bu ajanı ekleyince hangi emergence değişir?" sorusunu yanıtlayamıyorsan ekleme — karmaşıklık bütçeni koru.
