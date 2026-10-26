# contra-revenue-flux-analyzer

**MoM and QoQ variance analysis on gross-to-net revenue components with Model N anomaly detection.**

Built to reflect revenue accounting work at a Fortune 500 semiconductor company. Analyzes rebates, volume incentives, price protection, Special Price Adjustments (SPAs), and returns & allowances — and flags system-driven calculation anomalies from Model N versus true business changes.

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE) [![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org) [![Tests: pytest](https://img.shields.io/badge/Tests-pytest-green.svg)](tests/) [![100% Local](https://img.shields.io/badge/Data%20Privacy-100%25%20Local-brightgreen.svg)](#data-privacy)

---

## Live Demo
**[Try it live →](https://www.wong.cpa/contra-revenue-flux-analyzer/src/)**. Or open `src/index.html` locally → drop `tests/fixtures/contra_revenue_data.csv` → toggle QoQ/MoM → select period pair.

---

## Features

| Feature | Detail |
|---|---|
| Gross-to-net waterfall | Visual bar chart of all contra revenue components |
| MoM and QoQ toggle | Switch between monthly and quarterly analysis |
| Period pair selector | Compare any two periods in the dataset |
| Model N anomaly detection | Flags SPA January spikes, SPA-revenue disconnects, PP anomalies |
| Auto commentary | Pre-written flux commentary templates for reporting packages |
| CSV export | Full flux table for all periods |

---

## Repository Structure

```
contra-revenue-flux-analyzer/
├── src/
│   ├── index.html               # Browser web app with waterfall + anomaly panel
│   └── contra_revenue_flux.py   # Python CLI
├── tests/
│   ├── test_contra_revenue_flux.py  # pytest suite — net calc, flux, anomalies, loading
│   └── fixtures/
│       └── contra_revenue_data.csv  # 4 quarters + 6 months of contra revenue data
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## Quick Start

**Web app:** `open src/index.html` → drop `tests/fixtures/contra_revenue_data.csv`.

**CLI:**
```bash
git clone https://github.com/wongcpa/contra-revenue-flux-analyzer.git
cd contra-revenue-flux-analyzer
python src/contra_revenue_flux.py
# Enter: tests/fixtures/contra_revenue_data.csv
```

**Tests:** `pip install pytest && pytest tests/ -v`

---

## Input CSV Format

| Column | Description |
|---|---|
| `period` | Period label (e.g. `Q1-2025`, `Jan-2025`) |
| `period_type` | `quarterly` or `monthly` |
| `gross_revenue` | Gross revenue (USD thousands) |
| `rebates` | Rebate accruals |
| `volume_incentives` | Volume incentive programs |
| `price_protection` | Price protection reserves |
| `special_price_adj_spa` | Model N SPA accruals |
| `returns_allowances` | Returns and allowances |
| `other_contra` | Other contra revenue |

---

## Model N Anomaly Rules

| Rule | Trigger | Severity |
|---|---|---|
| SPA January spike | SPA increases >50% in January | HIGH |
| SPA-revenue disconnect | SPA swings >40% without revenue change | MEDIUM |
| Price protection anomaly | PP increases >60% while revenue is flat | MEDIUM |

---

## Standards Applied
- **ASC 606** — Variable consideration estimated using expected value / most likely amount
- **SAB Topic 13** — Channel inventory and price protection accrual
- **SOX** — Audit-ready flux documentation and commentary templates

---

## Data Privacy
All processing is local. No revenue data is uploaded to any server.

---

## Author

**Jimmy Wong, CPA (WA), CPA (Canada)**
[www.wong.cpa](https://www.wong.cpa) · [LinkedIn](https://www.linkedin.com/in/wongjimmy/) · [GitHub @wongcpa](https://github.com/wongcpa)
