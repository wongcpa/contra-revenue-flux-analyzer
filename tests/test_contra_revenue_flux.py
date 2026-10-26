"""
tests/test_contra_revenue_flux.py
===================================
Pytest test suite for the Contra Revenue Flux Analyzer.
Tests: net revenue calc, flux computation, anomaly detection, CSV loading.
Run: pytest tests/ -v
"""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from contra_revenue_flux import compute_net, compute_flux, detect_anomalies, load_data, CONTRA_LINES

def make_period(gross, rebates=0, vol_inc=0, price_prot=0, spa=0, returns=0, other=0):
    return {"gross_revenue":gross,"rebates":rebates,"volume_incentives":vol_inc,
            "price_protection":price_prot,"special_price_adj_spa":spa,
            "returns_allowances":returns,"other_contra":other}

class TestNetRevenue:
    def test_no_contra(self):
        assert compute_net(make_period(100_000)) == 100_000
    def test_all_contra_deducted(self):
        d = make_period(200_000,10_000,5_000,1_000,2_000,1_500,500)
        assert compute_net(d) == 200_000-10_000-5_000-1_000-2_000-1_500-500
    def test_net_cannot_exceed_gross(self):
        d = make_period(100_000, rebates=5_000)
        assert compute_net(d) <= 100_000
    def test_can_be_negative(self):
        assert compute_net(make_period(10_000, rebates=15_000)) == -5_000
    def test_all_lines_deducted(self):
        d = make_period(100_000)
        for k in CONTRA_LINES: d[k] = 1_000
        assert compute_net(d) == 100_000 - 1_000*len(CONTRA_LINES)

class TestFlux:
    def test_flat_period_zero_change(self):
        d = make_period(100_000, rebates=5_000)
        flux = compute_flux(d, d)
        assert flux["gross_revenue"]["change"] == 0
    def test_increase_positive(self):
        flux = compute_flux(make_period(120_000), make_period(100_000))
        assert flux["gross_revenue"]["change"] == 20_000
    def test_decrease_negative(self):
        flux = compute_flux(make_period(80_000), make_period(100_000))
        assert flux["gross_revenue"]["change"] == -20_000
    def test_pct_correct(self):
        flux = compute_flux(make_period(110_000), make_period(100_000))
        assert flux["gross_revenue"]["pct_chg"] == pytest.approx(10.0, rel=1e-2)
    def test_zero_prior_no_division_error(self):
        flux = compute_flux(make_period(100_000, spa=5_000), make_period(100_000, spa=0))
        assert flux["special_price_adj_spa"]["pct_chg"] == 0
    def test_direction_up(self):
        flux = compute_flux(make_period(110_000), make_period(100_000))
        assert flux["gross_revenue"]["direction"] == "▲"
    def test_direction_down(self):
        flux = compute_flux(make_period(90_000), make_period(100_000))
        assert flux["gross_revenue"]["direction"] == "▼"
    def test_direction_flat(self):
        d = make_period(100_000)
        assert compute_flux(d, d)["gross_revenue"]["direction"] == "—"
    def test_all_keys_present(self):
        flux = compute_flux(make_period(100_000), make_period(100_000))
        assert ({"gross_revenue"} | set(CONTRA_LINES)).issubset(set(flux.keys()))

class TestAnomalyDetection:
    def test_jan_spa_spike_high(self):
        prior = make_period(100_000, spa=2_000)
        curr  = make_period(102_000, spa=5_000)
        anoms = detect_anomalies("Jan-2025", compute_flux(curr, prior))
        assert any(a["severity"] == "HIGH" for a in anoms)
    def test_jan_spike_below_threshold_no_flag(self):
        prior = make_period(100_000, spa=2_000)
        curr  = make_period(102_000, spa=2_800)
        anoms = detect_anomalies("Jan-2025", compute_flux(curr, prior))
        assert not any("January" in a.get("description","") for a in anoms)
    def test_spa_disconnect_medium(self):
        prior = make_period(100_000, spa=2_000)
        curr  = make_period(101_000, spa=5_000)
        anoms = detect_anomalies("Mar-2025", compute_flux(curr, prior))
        assert any(a["severity"] == "MEDIUM" for a in anoms)
    def test_pp_anomaly_medium(self):
        prior = make_period(100_000, price_prot=1_000)
        curr  = make_period(101_000, price_prot=2_500)
        anoms = detect_anomalies("Feb-2025", compute_flux(curr, prior))
        assert any("price_protection" in a.get("line","") for a in anoms)
    def test_normal_growth_no_anomaly(self):
        prior = make_period(100_000, rebates=5_000, spa=2_000)
        curr  = make_period(105_000, rebates=5_250, spa=2_100)
        anoms = detect_anomalies("Apr-2025", compute_flux(curr, prior))
        assert len(anoms) == 0
    def test_anomaly_has_required_fields(self):
        prior = make_period(100_000, spa=2_000)
        curr  = make_period(102_000, spa=5_000)
        anoms = detect_anomalies("Jan-2025", compute_flux(curr, prior))
        for a in anoms:
            assert all(k in a for k in ["severity","description","commentary"])

class TestDataLoading:
    @pytest.fixture(autouse=True)
    def fx(self):
        self.fp = os.path.join(os.path.dirname(__file__),'..','fixtures','contra_revenue_data.csv')
    def test_loads_without_error(self):
        q, m = load_data(self.fp); assert len(q) > 0 or len(m) > 0
    def test_quarterly_separated(self):
        q, _ = load_data(self.fp); assert len(q) >= 4
    def test_monthly_separated(self):
        _, m = load_data(self.fp); assert len(m) >= 3
    def test_quarterly_labels_have_Q(self):
        q, _ = load_data(self.fp)
        assert all("Q" in p for p in q)
    def test_all_contra_lines_present(self):
        q, _ = load_data(self.fp)
        first = list(q.values())[0]
        assert all(k in first for k in CONTRA_LINES)
    def test_gross_revenue_positive(self):
        q, m = load_data(self.fp)
        assert all(d["gross_revenue"] > 0 for d in {**q,**m}.values())
