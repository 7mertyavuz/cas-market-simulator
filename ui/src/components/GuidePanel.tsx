const sections = [
  {
    title: 'Bu panel ne işe yarar?',
    body: `CAS Market Dashboard, karmaşık uyarlanabilir sistem (CAS) lensiyle piyasayı gözlemlemeni sağlar. Makro sentiment, mikroyapı (order flow & book) ve teknik faktörleri tek bir "analyst card" üzerinde birleştirir. Amaç otomatik işlem sinyali üretmek DEĞİL, piyasanın yapısını daha hızlı anlamana yardım etmektir.`,
  },
  {
    title: 'Sembol arama',
    body: `Üstteki arama çubuğuna istediğin hisse, coin veya para birimi sembolünü yazıp "Analiz Et"e bas. Hızlı seçim çiplerinden (BTC, ETH, SOL vb.) de geçiş yapabilirsin. Tüm paneller o sembol için güncellenir.`,
  },
  {
    title: 'Analist Kartı ne gösteriyor?',
    body: `Seçtiğin sembolün LONG / SHORT / NEUTRAL yön tahmini, güven skoru, faktör oyları (trend, momentum, hacim, orderbook, sentiment), tespit edilen formasyonlar ve önerilen risk parametrelerini (stop/take/size) gösterir. Yüksek confidence, modelin faktörler arasında uzlaştığı anlamına gelir; %100 değildir ve yanılabilir.`,
  },
  {
    title: 'Mikroyapı paneli',
    body: `Order flow ve defter okuma metriklerini bir arada sunar. Flow imbalance alım/satış baskısını, VPIN toksisiteyi, whale net büyük oyuncuların net USD akışını, actor mix katılımcı dağılımını gösterir. Book State bölümünde spread, microprice, depth imbalance, OFI (order flow imbalance), book slope, kyle lambda (piyasa etkisi), iceberg/spoof şüphe skorları ve likidite haritası çarpıklığı yer alır.`,
  },
  {
    title: 'Sentiment & Şoklar paneli',
    body: `Seçilen varlık için metin tabanlı duygu analizi (polarity, intensity, confidence), duygu dağılımı (fear/greed/uncertainty) ve varsa Fed tonu gösterilir. Aktif şoklar panosu ise ani panik, öfori, Fed tonu değişimi veya anlatı kayması gibi dışsal olayların büyüklüğünü ve yarı ömrünü listeler.`,
  },
  {
    title: 'CAS Laboratuvarı',
    body: `Simüle edilmiş fiyat hareketini ve "crowd emergence" skorunu görselleştirir. Panik şoku veya balina emri butonları ileride simülasyona dışsal bir etki enjekte edecek; şu an gösterim amaçlıdır.`,
  },
  {
    title: 'HITL Onay (Human-in-the-Loop)',
    body: `Modelin önerdiği yönü ve büyüklüğü operatör olarak gözden geçirip override edebileceğin ekrandır. Pozisyon büyüklüğü slider'ı, override yön butonları ve operatör notu alanı içerir. Onayla butonu ileride backend'e audit kaydı gönderecek; şu an mock çalışır.`,
  },
  {
    title: 'Önemli uyarı',
    body: `Burada gösterilen hiçbir içerik yatırım tavsiyesi değildir. Modeller simülasyon ve/veya sınırlı veriyle çalışır; gerçek sermaye ile işlem yapmadan önce kendi araştırmanı ve risk yönetimini uygula.`,
  },
]

export default function GuidePanel() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-gradient-to-r from-accent/10 to-accent-blue/10 border border-accent/20 rounded-2xl p-6">
        <h2 className="text-2xl font-bold text-accent mb-2">CAS Market Kılavuzu</h2>
        <p className="text-text-muted">
          Dashboard'u doğru kullanmak ve her metriğin ne anlama geldiğini öğrenmek için aşağıdaki bölümleri okuyun.
        </p>
      </div>

      <div className="grid gap-4">
        {sections.map((s, i) => (
          <div key={i} className="bg-surface border border-border rounded-xl p-5 hover:border-accent/30 transition-colors">
            <h3 className="text-lg font-semibold text-text mb-2 flex items-center gap-2">
              <span className="text-accent">{i + 1}.</span> {s.title}
            </h3>
            <p className="text-text-muted leading-relaxed">{s.body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
