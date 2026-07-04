"""Portfoy insasi: Hierarchical Risk Parity (HRP) + korelasyon limiti + risk butcesi.

Faz 9 amaci: tek sembolden portfoye gecis. Uc adim:
  1. HRP agirliklari -- kovaryans matrisinden hiyerarsik kumeleme +
     quasi-diagonalizasyon + rekursif bolme (Lopez de Prado, 2016).
     Markowitz'in aksine matris tersine cevirme (inversion) gerektirmez,
     bu yuzden kotu-kosullu (ill-conditioned) korelasyon matrislerinde
     daha stabildir.
  2. Korelasyon limiti -- tek varlik ve yuksek-korelasyonlu cift agirlik
     tavanlari (konsantrasyon riskini sinirlar).
  3. Risk butcesi -- portfoy volatilitesini hedef gunluk volatiliteye
     olceklendirir (yalnizca kucultme yonunde, kaldirac varsayilmaz).

Bagimlilik: yalnizca numpy. scipy YOK -- kumeleme sifirdan yazildi.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


# ─── 1) Hiyerarsik kumeleme (tek-baglantili / single-linkage, scipy'siz) ───


def _single_linkage(dist: np.ndarray, n: int) -> dict[int, tuple[int, int]]:
    """Basit O(n^3) tek-baglantili aglomeratif kumeleme.

    scipy.cluster.hierarchy.linkage'in tam ozellikli bir esdegeri degil;
    yalnizca HRP'nin ihtiyac duydugu 'children' esleme sozlugunu uretir:
    yeni_kume_id -> (alt_id_1, alt_id_2). Yapraklar 0..n-1, ic dugumler
    n..2n-2 (kok = 2n-2).
    """
    D: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j in range(i + 1, n):
            D[(i, j)] = float(dist[i, j])

    current_ids = list(range(n))
    children: dict[int, tuple[int, int]] = {}
    next_id = n

    while len(current_ids) > 1:
        best_pair = None
        best_d = math.inf
        for a_idx in range(len(current_ids)):
            for b_idx in range(a_idx + 1, len(current_ids)):
                a, b = current_ids[a_idx], current_ids[b_idx]
                key = (a, b) if a < b else (b, a)
                d = D[key]
                if d < best_d:
                    best_d = d
                    best_pair = (a, b)

        a, b = best_pair
        new_id = next_id
        next_id += 1
        children[new_id] = (a, b)

        for c in current_ids:
            if c == a or c == b:
                continue
            key_a = (a, c) if a < c else (c, a)
            key_b = (b, c) if b < c else (c, b)
            d_new = min(D[key_a], D[key_b])  # single-linkage: minimum mesafe
            key_new = (new_id, c) if new_id < c else (c, new_id)
            D[key_new] = d_new

        current_ids = [c for c in current_ids if c != a and c != b]
        current_ids.append(new_id)

    return children


def _quasi_diag_order(children: dict[int, tuple[int, int]], n: int) -> list[int]:
    """Dendrogramin kokunden derinlik-oncelikli genisleterek yaprak (varlik)
    sirasini cikarir -- benzer varliklari birbirine yakin siralar
    (blok-koesgen kovaryans yapisi).
    """
    root_id = 2 * n - 2 if n > 1 else 0

    def expand(node_id: int) -> list[int]:
        if node_id < n:
            return [node_id]
        left, right = children[node_id]
        return expand(left) + expand(right)

    if n <= 1:
        return list(range(n))
    return expand(root_id)


# ─── 2) Rekursif bolme (recursive bisection) ile agirliklandirma ───


def _cluster_variance(cov: np.ndarray, items: list[int]) -> float:
    """Bir kume icin ters-varyans agirlikli (inverse-variance) portfoy varyansi."""
    cov_slice = cov[np.ix_(items, items)]
    diag = np.diag(cov_slice).copy()
    diag[diag <= 0] = 1e-12
    ivp = 1.0 / diag
    ivp = ivp / ivp.sum()
    w = ivp.reshape(-1, 1)
    var = float((w.T @ cov_slice @ w).item())
    return max(var, 0.0)


def _recursive_bisection(cov: np.ndarray, sorted_items: list[int]) -> np.ndarray:
    n = len(sorted_items)
    weights = np.ones(n)
    idx_map = {item: i for i, item in enumerate(sorted_items)}
    clusters: list[list[int]] = [sorted_items]

    while clusters:
        next_clusters: list[list[int]] = []
        for c in clusters:
            if len(c) <= 1:
                continue
            mid = len(c) // 2
            c0, c1 = c[:mid], c[mid:]
            var0 = _cluster_variance(cov, c0)
            var1 = _cluster_variance(cov, c1)
            total = var0 + var1
            alpha = (1.0 - var0 / total) if total > 0 else 0.5
            for item in c0:
                weights[idx_map[item]] *= alpha
            for item in c1:
                weights[idx_map[item]] *= (1.0 - alpha)
            next_clusters.append(c0)
            next_clusters.append(c1)
        clusters = next_clusters

    return weights


def hrp_weights(returns: np.ndarray, symbols: list[str] | None = None) -> dict[str, float]:
    """Getiri matrisinden (n_obs x n_assets) HRP agirliklarini hesaplar.

    Tek varlik durumunda agirlik 1.0'dir (bolunecek bir sey yok).
    """
    returns = np.asarray(returns, dtype=float)
    if returns.ndim == 1:
        returns = returns.reshape(-1, 1)
    n_assets = returns.shape[1]
    if symbols is None:
        symbols = [f"asset_{i}" for i in range(n_assets)]
    if len(symbols) != n_assets:
        raise ValueError("symbols uzunlugu returns'un varlik sayisiyla eslesmeli")

    if n_assets == 1:
        return {symbols[0]: 1.0}

    cov = np.cov(returns, rowvar=False)
    corr = np.corrcoef(returns, rowvar=False)
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)

    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, None))
    np.fill_diagonal(dist, 0.0)

    children = _single_linkage(dist, n_assets)
    order = _quasi_diag_order(children, n_assets)
    raw_weights = _recursive_bisection(cov, order)

    total = raw_weights.sum()
    if total <= 0:
        raw_weights = np.ones(n_assets) / n_assets
        total = 1.0
    raw_weights = raw_weights / total

    return {symbols[order[i]]: float(raw_weights[i]) for i in range(n_assets)}


# ─── 3) Korelasyon limiti ───


def apply_correlation_limit(
    weights: dict[str, float],
    corr: np.ndarray,
    symbols: list[str],
    *,
    max_pairwise_corr: float = 0.85,
    max_combined_weight: float = 0.35,
    max_single_weight: float = 0.4,
) -> dict[str, float]:
    """Konsantrasyon riskini sinirlar:
    1. Tek bir varligin agirligi max_single_weight'i asamaz.
    2. Korelasyonu max_pairwise_corr'un uzerindeki cift, birlesik agirlikta
       max_combined_weight tavanina tabidir (oransal olcekleme).

    Onemli tasarim karari: kirpilan fazla agirlik DIGER varliklara geri
    dagitilmaz (bu, kisitlamanin amacini bosa cikarir -- ornegin A %70'ten
    %40'a kirpilip kalan %30 yeniden A'ya orantili dagitilirsa A yine
    tavanin uzerine cikar). Bunun yerine kirpilan fazlalik YATIRILMAMIS
    (nakit) olarak birakilir; sonuc toplami 1.0'dan KUCUK OLABILIR.
    Cagiran taraf `sum(weights.values())` ile nakit oranini gorebilir.
    """
    w = {s: float(weights.get(s, 0.0)) for s in symbols}
    n = len(symbols)

    if n > 1:
        # tek varlik durumunda "konsantrasyon" kavraminin bir anlami yok
        # (secilecek baska alternatif yok) -- tavan yalnizca n>1 icin uygulanir.
        for s in symbols:
            if w[s] > max_single_weight:
                w[s] = max_single_weight

    for i in range(n):
        for j in range(i + 1, n):
            si, sj = symbols[i], symbols[j]
            if corr[i, j] >= max_pairwise_corr:
                combined = w[si] + w[sj]
                if combined > max_combined_weight and combined > 1e-12:
                    scale = max_combined_weight / combined
                    w[si] *= scale
                    w[sj] *= scale

    return w


# ─── 4) Gunluk risk butcesi olceklendirme ───


def scale_to_risk_budget(
    weights: dict[str, float],
    cov: np.ndarray,
    symbols: list[str],
    *,
    target_daily_vol: float = 0.02,
) -> tuple[dict[str, float], float]:
    """Portfoy agirliklarini hedef gunluk volatiliteye olceklendirir.

    Yalnizca KUCULTME yapar (scale <= 1.0) -- kaldirac/buyutme varsayilmaz;
    portfoy zaten hedefin altindaysa agirliklar degismeden doner.
    """
    w_vec = np.array([weights.get(s, 0.0) for s in symbols])
    port_var = float(w_vec @ cov @ w_vec)
    port_vol = math.sqrt(max(port_var, 0.0))

    if port_vol <= 1e-12:
        return dict(weights), 1.0

    scale = min(target_daily_vol / port_vol, 1.0)
    scaled = {k: v * scale for k, v in weights.items()}
    return scaled, scale


# ─── 5) Uctan-uca portfoy insasi ───


@dataclass
class PortfolioAllocation:
    symbols: list[str]
    hrp_weights: dict[str, float]
    limited_weights: dict[str, float]
    final_weights: dict[str, float]
    portfolio_daily_vol: float
    risk_scale: float
    warnings: list[str] = field(default_factory=list)


def build_portfolio(
    returns: np.ndarray,
    symbols: list[str],
    *,
    max_pairwise_corr: float = 0.85,
    max_combined_weight: float = 0.35,
    max_single_weight: float = 0.4,
    target_daily_vol: float = 0.02,
) -> PortfolioAllocation:
    """HRP -> korelasyon limiti -> risk butcesi zincirini calistirip
    nihai portfoy agirliklarini uretir.
    """
    returns = np.asarray(returns, dtype=float)
    warnings: list[str] = []

    hrp_w = hrp_weights(returns, symbols)

    n_assets = len(symbols)
    if n_assets > 1:
        corr = np.corrcoef(returns, rowvar=False)
        corr = np.clip(corr, -1.0, 1.0)
        np.fill_diagonal(corr, 1.0)
    else:
        corr = np.array([[1.0]])
        warnings.append("tek varlik: korelasyon limiti anlamsiz, atlandi")

    limited_w = apply_correlation_limit(
        hrp_w,
        corr,
        symbols,
        max_pairwise_corr=max_pairwise_corr,
        max_combined_weight=max_combined_weight,
        max_single_weight=max_single_weight,
    )

    cov = np.cov(returns, rowvar=False) if n_assets > 1 else np.array([[np.var(returns)]])
    final_w, scale = scale_to_risk_budget(
        limited_w, cov, symbols, target_daily_vol=target_daily_vol
    )
    if scale < 1.0:
        warnings.append(
            f"portfoy volatilitesi hedefi asiyordu, agirliklar {scale:.3f} ile olceklendi"
        )

    w_vec = np.array([final_w.get(s, 0.0) for s in symbols])
    port_vol = math.sqrt(max(float(w_vec @ cov @ w_vec), 0.0))

    return PortfolioAllocation(
        symbols=list(symbols),
        hrp_weights=hrp_w,
        limited_weights=limited_w,
        final_weights=final_w,
        portfolio_daily_vol=port_vol,
        risk_scale=scale,
        warnings=warnings,
    )
