"""
contra_revenue_flux_analyzer.py
================================
Contra Revenue & Gross-to-Net Flux Analyzer — Semiconductor Revenue Accounting

Usage:
  python contra_revenue_flux_analyzer.py

You will be prompted for:
  - Contra revenue data CSV file

Expected CSV columns:
  period, period_type, gross_revenue, rebates, volume_incentives,
  price_protection, special_price_adj_spa, returns_allowances, other_contra

  period_type values: 'quarterly' or 'monthly'
  All amounts in USD thousands.

Test fixture: contra_revenue_data.csv

Author: Jimmy Wong, CPA
DATA PRIVACY: All data is processed locally. No data leaves your machine.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# SECTION 1: CONSTANTS
# ---------------------------------------------------------------------------

CONTRA_LINES = [
    "rebates", "volume_incentives", "price_protection",
    "special_price_adj_spa", "returns_allowances", "other_contra"
]

LINE_LABELS = {
    "gross_revenue":         "Gross Revenue",
    "rebates":               "Rebates & Volume Incentives (Base)",
    "volume_incentives":     "Volume Incentive Programs",
    "price_protection":      "Price Protection",
    "special_price_adj_spa": "Special Price Adjustments (SPA/Model N)",
    "returns_allowances":    "Returns & Allowances",
    "other_contra":          "Other Contra Revenue",
}

EXPECTED_COLUMNS = {
    "period", "period_type", "gross_revenue", "rebates",
    "volume_incentives", "price_protection", "special_price_adj_spa",
    "returns_allowances", "other_contra"
}

# ---------------------------------------------------------------------------
# SECTION 2: FILE INPUT WITH RETRY LOGIC
# ---------------------------------------------------------------------------

def prompt_for_file(max_attempts: int = 3) -> str:
    """
    Prompt for the contra revenue CSV file path.
    Re-prompts up to max_attempts times on failure.
    """
    print("\n" + "=" * 64)
    print("  CONTRA REVENUE FLUX ANALYZER")
    print("=" * 64)
    print("\nTest fixture: contra_revenue_data.csv")
    print("Expected columns:", ", ".join(sorted(EXPECTED_COLUMNS)))

    for attempt in range(1, max_attempts + 1):
        raw = input("\nContra revenue data CSV: ").strip()
        path = Path(raw)

        if not path.exists():
            print(f"  ERROR: File not found: '{raw}'")
        elif path.suffix.lower() != ".csv":
            print(f"  ERROR: Expected .csv file, got '{path.suffix}'")
        else:
            try:
                with open(path, newline="", encoding="utf-8-sig") as f:
                    headers = set(csv.DictReader(f).fieldnames or [])
                    missing = EXPECTED_COLUMNS - headers
                    if missing:
                        print(f"  ERROR: Missing columns: "
                              f"{', '.join(sorted(missing))}")
                    else:
                        return str(path)
            except Exception as e:
                print(f"  ERROR: Could not read file: {e}")

        if attempt < max_attempts:
            print(f"  Attempt {attempt}/{max_attempts}. Please try again.")

    print(f"\n  FATAL: Maximum attempts ({max_attempts}) reached. Exiting.")
    sys.exit(1)


def prompt_for_output(default: str = "contra_revenue_flux.csv") -> str:
    raw = input(f"\nOutput CSV filename [{default}]: ").strip()
    return raw if raw else default


# ---------------------------------------------------------------------------
# SECTION 3: DATA LOADING
# ---------------------------------------------------------------------------

def load_data(filepath: str) -> Tuple[
        Dict[str, Dict], Dict[str, Dict]]:
    """
    Load contra revenue CSV into quarterly and monthly dicts.

    Returns:
        (quarterly_data, monthly_data) dicts keyed by period label.
    """
    quarterly, monthly = {}, {}
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            period = row["period"].strip()
            ptype  = row["period_type"].strip().lower()
            data   = {
                col: float(row[col] or 0)
                for col in ["gross_revenue"] + CONTRA_LINES
            }
            if ptype == "quarterly":
                quarterly[period] = data
            elif ptype == "monthly":
                monthly[period] = data
    return quarterly, monthly


# ---------------------------------------------------------------------------
# SECTION 4: CALCULATION ENGINE
# ---------------------------------------------------------------------------

def compute_net(period_data: Dict) -> float:
    return period_data["gross_revenue"] - sum(
        period_data[k] for k in CONTRA_LINES)


def compute_flux(current: Dict, prior: Dict) -> Dict:
    """Compute period-over-period variance for all lines."""
    flux = {}
    for line in ["gross_revenue"] + CONTRA_LINES:
        curr_val  = current.get(line, 0.0)
        prior_val = prior.get(line, 0.0)
        change    = curr_val - prior_val
        pct_chg   = ((change / prior_val) * 100) if prior_val != 0 else 0.0
        flux[line] = {
            "current":  curr_val,
            "prior":    prior_val,
            "change":   change,
            "pct_chg":  round(pct_chg, 1),
            "direction": "▲" if change > 0 else ("▼" if change < 0 else "—"),
        }
    return flux


def detect_anomalies(period: str, flux: Dict) -> List[Dict]:
    """Detect Model N system-driven anomalies."""
    anomalies = []
    spa = flux.get("special_price_adj_spa", {})
    spa_pct = abs(spa.get("pct_chg", 0))
    pp  = flux.get("price_protection", {})
    rev = flux.get("gross_revenue", {})

    if "Jan" in period and spa_pct > 50:
        anomalies.append({
            "severity": "HIGH",
            "line": "special_price_adj_spa",
            "description": "SPA spike in January — likely Model N Q4 year-end true-up batch",
            "commentary": (
                "SPA increase consistent with Model N year-end batch recalculation. "
                "Validate against Model N SPA report to confirm prior-period catch-up vs. "
                "current-period activity. Book adjustment if >30 days stale."
            ),
        })
    elif spa_pct > 40:
        anomalies.append({
            "severity": "MEDIUM",
            "line": "special_price_adj_spa",
            "description": "SPA-revenue disconnect — possible Model N config change",
            "commentary": (
                "SPA change disproportionate to revenue movement. Common causes: "
                "(1) Model N rate table update applied retroactively, "
                "(2) distributor tier re-classification, "
                "(3) system recalculation due to deal registration correction."
            ),
        })

    if pp.get("pct_chg", 0) > 60 and rev.get("pct_chg", 0) < 10:
        anomalies.append({
            "severity": "MEDIUM",
            "line": "price_protection",
            "description": "Price protection elevated without revenue decline",
            "commentary": (
                "Price protection accrual elevated. Verify against distributor inventory "
                "reports. Common Model N issue: system accrues on stale inventory not yet "
                "confirmed. Cross-reference with channel POS data."
            ),
        })
    return anomalies


# ---------------------------------------------------------------------------
# SECTION 5: REPORTING
# ---------------------------------------------------------------------------

def print_flux_report(current_period: str, prior_period: str,
                      current_data: Dict, prior_data: Dict,
                      flux_type: str) -> None:
    """Print a formatted flux analysis report."""
    flux      = compute_flux(current_data, prior_data)
    anomalies = detect_anomalies(current_period, flux)
    curr_net  = compute_net(current_data)
    prior_net = compute_net(prior_data)
    net_chg   = curr_net - prior_net
    net_pct   = ((net_chg / prior_net) * 100) if prior_net else 0

    div = "=" * 80
    print(f"\n{div}")
    print(f"  CONTRA REVENUE FLUX — {flux_type}")
    print(f"  Current: {current_period}   Prior: {prior_period}   (USD Thousands)")
    print(div)

    hdr = (f"  {'Line Item':<40} {'Prior':>10} {'Current':>10} "
           f"{'$ Chg':>10} {'% Chg':>8} {'Dir':>4}")
    print(hdr)
    print("  " + "-" * 76)

    all_lines = ["gross_revenue"] + CONTRA_LINES
    for line in all_lines:
        if line not in flux:
            continue
        f      = flux[line]
        label  = LINE_LABELS.get(line, line)
        flag   = " ⚠" if any(a["line"] == line for a in anomalies) else ""
        sep    = "\n  " + "-" * 76 if line == "gross_revenue" else ""
        print(f"  {label + flag:<40} ${f['prior']:>9,.0f} "
              f"${f['current']:>9,.0f} ${f['change']:>+9,.0f} "
              f"{f['pct_chg']:>+7.1f}% {f['direction']:>4}")
        if sep:
            print(sep)

    print("  " + "-" * 76)
    print(f"  {'NET REVENUE':<40} ${prior_net:>9,.0f} ${curr_net:>9,.0f} "
          f"${net_chg:>+9,.0f} {net_pct:>+7.1f}%")

    curr_pct  = (current_data["gross_revenue"] - curr_net) / current_data["gross_revenue"] * 100
    prior_pct = (prior_data["gross_revenue"]   - prior_net) / prior_data["gross_revenue"] * 100
    print(f"\n  Contra as % of Gross — Prior: {prior_pct:.1f}%   "
          f"Current: {curr_pct:.1f}%   Change: {curr_pct - prior_pct:+.1f}pp")

    if anomalies:
        print(f"\n  ⚠  MODEL N ANOMALY FLAGS ({len(anomalies)})")
        print("  " + "-" * 76)
        for a in anomalies:
            print(f"\n  [{a['severity']}] {a['description']}")
            print(f"  Commentary: {a['commentary']}")
    else:
        print("\n  ✔ No Model N anomalies detected.")

    print(f"\n{div}")


def export_csv(all_rows: List[Dict], filepath: str) -> None:
    """Export flux summary to CSV."""
    if not all_rows:
        return
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"  ✔ Flux export saved to: {filepath}")


# ---------------------------------------------------------------------------
# SECTION 6: MAIN
# ---------------------------------------------------------------------------

def main():
    input_path  = prompt_for_file()
    output_path = prompt_for_output()

    print(f"\nLoading data from: {input_path}")
    quarterly, monthly = load_data(input_path)

    q_periods = list(quarterly.keys())
    m_periods = list(monthly.keys())

    # QoQ pairs
    q_pairs = [(q_periods[i], q_periods[i-1])
               for i in range(1, len(q_periods))]
    # MoM pairs
    m_pairs = [(m_periods[i], m_periods[i-1])
               for i in range(1, len(m_periods))]

    if q_pairs:
        print("\n" + "=" * 80)
        print("  QUARTERLY (QoQ) FLUX ANALYSIS")
        print("=" * 80)
        for curr_q, prior_q in q_pairs:
            print_flux_report(curr_q, prior_q, quarterly[curr_q],
                              quarterly[prior_q], "QoQ")

    if m_pairs:
        print("\n" + "=" * 80)
        print("  MONTHLY (MoM) FLUX ANALYSIS")
        print("=" * 80)
        for curr_m, prior_m in m_pairs:
            print_flux_report(curr_m, prior_m, monthly[curr_m],
                              monthly[prior_m], "MoM")

    # Build CSV rows
    summary_rows = []
    for curr_q, prior_q in q_pairs:
        flux = compute_flux(quarterly[curr_q], quarterly[prior_q])
        for line, f in flux.items():
            summary_rows.append({
                "flux_type": "QoQ", "period": curr_q,
                "prior_period": prior_q, "line": line,
                "prior": f["prior"], "current": f["current"],
                "change": f["change"], "pct_chg": f["pct_chg"],
            })

    export_csv(summary_rows, output_path)


if __name__ == "__main__":
    # Report symbols (✔, →) must print even when output is redirected on Windows.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
