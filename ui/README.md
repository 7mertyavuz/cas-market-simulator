# CAS Market Dashboard UI

React + TypeScript + Vite + Tailwind v4 + Recharts tabanlı CAS Market (Faz FE) arayüzü.

## Hızlı Başlangıç

```bash
npm install
npm run dev
```

Tarayıcıda `http://localhost:5173` açılır.

## Komutlar

| Komut | Açıklama |
|-------|----------|
| `npm run dev` | Geliştirme sunucusu (Vite, `/v1` proxy ile backend'e yönlendirilir) |
| `npm run build` | Production build (`ui/dist`) |
| `npm run preview` | Build edilmiş uygulamayı önizle |
| `npm run test` | Vitest testlerini çalıştır |
| `npm run lint` | Oxlint ile kod kalitesi kontrolü |

## Backend Bağlantısı

Geliştirme sırasında Vite, `/v1` isteklerini `http://127.0.0.1:8000`'e proxy eder.

```bash
# Ayrı terminalde backend
python -m uvicorn cas_market_simulator.api.main:app --host 127.0.0.1 --port 8000
```

Mock veri yerine gerçek backend'i kullanmak için:

```bash
VITE_USE_MOCK=false npm run dev
```

Production'da FastAPI aynı domain altında `/v1` uçlarını serve eder ve statik `ui/dist`'i döndürür.

## Ekranlar

- **Analist Kartı**: Seçilen sembolün yön tahmini, güven skoru, faktör oyları, formasyonlar ve risk parametreleri.
- **Mikroyapı**: Order flow, actor mix, defter okuma metrikleri.
- **Sentiment & Şoklar**: Duygu analizi ve aktif piyasa şokları.
- **CAS Laboratuvarı**: Simülasyon, fiyat seyri ve crowd emergence skoru.
- **HITL Onay**: Model çıktısını operatör olarak gözden geçirme ve override.
- **Kılavuz**: Uygulama içi yardım ve metrik açıklamaları.

## Önemli Not

Yatırım tavsiyesi değildir.
