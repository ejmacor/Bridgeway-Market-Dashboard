"""
Weekly Market Update Dashboard  v3
====================================
Run with:  python -m streamlit run app.py
"""

import os
import re
import warnings
import requests
import feedparser
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from datetime import date, datetime, timedelta
from drilldown import render_drilldown, TAXONOMY

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Weekly Market Update",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY   = "#0B1F3A"
SLATE  = "#1E3A5F"
SILVER = "#8BA3BF"
WHITE  = "#F5F7FA"
GREEN  = "#1FAD6A"
RED    = "#D64045"
GOLD   = "#C8A96E"
BG     = "#0E1C2E"
CARD   = "#132840"
BLUE   = "#5BBFFF"
TEXT   = "#D8E4F0"   # bright readable body text

def hex_rgba(hex_color: str, alpha: float = 0.12) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
html, body, [class*="css"] {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: {BG};
    color: {TEXT};
}}
.stApp {{ background-color: {BG}; }}

/* ── Remove top whitespace ── */
.stApp > header {{ display: none !important; }}
.block-container {{
    padding-top: 12px !important;
    padding-bottom: 20px !important;
}}
[data-testid="stAppViewContainer"] > section > div {{
    padding-top: 12px !important;
}}

/* ── Cards ── */
.card {{
    background: {CARD};
    border: 1px solid {SLATE};
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 8px;
}}
.card-label {{
    font-size: 10px;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: {SILVER};
    margin-bottom: 4px;
}}
.card-value {{
    font-size: 24px;
    font-weight: 700;
    color: {WHITE};
    line-height: 1.1;
}}
.up  {{ color: {GREEN}; font-size: 13px; font-weight: 600; }}
.dn  {{ color: {RED};   font-size: 13px; font-weight: 600; }}
.neu {{ color: {SILVER}; font-size: 13px; }}

/* ── Section headers ── */
.sec {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {GOLD};
    border-bottom: 1px solid {SLATE};
    padding-bottom: 7px;
    margin: 28px 0 14px 0;
}}

/* ── Summary box ── */
.sbox {{
    background: {CARD};
    border-left: 3px solid {GOLD};
    border-radius: 6px;
    padding: 16px 20px;
    font-size: 13px;
    line-height: 1.8;
    color: {TEXT};
}}
.sbox ul {{ margin: 4px 0 0 16px; padding: 0; }}
.sbox li {{ margin-bottom: 6px; color: {TEXT}; }}

/* ── News ── */
.ncard {{
    background: {CARD};
    border: 1px solid {SLATE};
    border-radius: 6px;
    padding: 11px 14px;
    margin-bottom: 7px;
}}
.ntitle a {{
    color: {WHITE};
    text-decoration: none;
    font-size: 13px;
    font-weight: 600;
    line-height: 1.4;
}}
.ntitle a:hover {{ color: {GOLD}; }}
.nmeta {{ color: {SILVER}; font-size: 10px; margin-top: 3px; }}
.nbody {{ color: {TEXT}; font-size: 11px; margin-top: 5px; line-height: 1.5; }}

/* ── Calendar ── */
.cevent {{
    background: {CARD};
    border-left: 2px solid {GOLD};
    border-radius: 4px;
    padding: 7px 12px;
    margin-bottom: 5px;
    font-size: 12px;
    color: {TEXT};
}}
.cdate {{ color: {GOLD}; font-size: 10px; font-weight: 700; letter-spacing: 0.06em; }}

/* ── Sidebar – force visible text & inputs ── */
section[data-testid="stSidebar"] {{
    background: {CARD} !important;
}}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {{
    color: {WHITE} !important;
}}
section[data-testid="stSidebar"] input {{
    background-color: {NAVY} !important;
    color: {WHITE} !important;
    border: 1px solid {SLATE} !important;
    border-radius: 6px !important;
}}
section[data-testid="stSidebar"] input::placeholder {{
    color: {SILVER} !important;
}}

/* ── Dataframe text ── */
[data-testid="stDataFrame"] {{ color: {WHITE}; }}

/* ── General text ── */
p, li, span {{ color: {TEXT}; }}

/* ── Remove ALL column divider/border lines ── */
[data-testid="stHorizontalBlock"] > div {{
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    box-shadow: none !important;
}}
[data-testid="column"] {{
    border: none !important;
    box-shadow: none !important;
}}
hr, [data-testid="stDivider"] {{ display: none !important; }}

/* ── Hide Streamlit branding but keep sidebar toggle visible ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* ── Multiselect: remove white background, match dark theme ── */
[data-testid="stMultiSelect"] > div,
[data-testid="stMultiSelect"] > div > div,
div[data-baseweb="select"] > div,
div[data-baseweb="popover"],
.stMultiSelect [data-baseweb="select"] {{
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
[data-testid="stMultiSelect"] {{
    background-color: transparent !important;
}}
/* Keep the tag pills (red boxes) but remove container background */
[data-baseweb="tag"] {{
    background-color: {RED} !important;
    border-color: {RED} !important;
}}
[data-baseweb="tag"] span {{
    color: {WHITE} !important;
}}
/* Hide the dropdown input area background */
div[data-baseweb="select"] input {{
    background: transparent !important;
}}
div[data-baseweb="select"] > div:first-child {{
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}}

/* ── All buttons: dark themed to match dashboard ── */
button[kind="secondary"],
button[kind="primary"],
.stButton > button,
div[data-testid="stButton"] > button {{
    background-color: {CARD} !important;
    color: {GOLD} !important;
    border: 1px solid {SLATE} !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    padding: 4px 10px !important;
    min-height: 32px !important;
    line-height: 1 !important;
    box-shadow: none !important;
    transition: border-color 0.15s, background-color 0.15s !important;
}}
button[kind="secondary"]:hover,
button[kind="primary"]:hover,
.stButton > button:hover,
div[data-testid="stButton"] > button:hover {{
    background-color: {SLATE} !important;
    border-color: {GOLD} !important;
    color: {WHITE} !important;
    box-shadow: none !important;
}}

/* ── Sidebar: always visible, never hide toggle ── */
[data-testid="collapsedControl"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    position: fixed !important;
    top: 50vh !important;
    left: 0px !important;
    z-index: 999999 !important;
    background-color: {CARD} !important;
    border: 2px solid {GOLD} !important;
    border-left: none !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 10px 5px !important;
    transform: translateY(-50%) !important;
    min-width: 24px !important;
    min-height: 48px !important;
    align-items: center !important;
    justify-content: center !important;
}}
[data-testid="collapsedControl"] svg {{
    fill: {GOLD} !important;
    color: {GOLD} !important;
    width: 18px !important;
    height: 18px !important;
}}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

INDEX_TICKERS = {
    "S&P 500":      "^GSPC",
    "Nasdaq":       "^IXIC",
    "Dow Jones":    "^DJI",
    "Russell 2000": "^RUT",
    "VIX":          "^VIX",
    "Dev. Markets": "EFA",
    "Emg. Markets": "EEM",
}

SECTOR_TICKERS = {
    "Technology":       "XLK",
    "Financials":       "XLF",
    "Healthcare":       "XLV",
    "Energy":           "XLE",
    "Consumer Disc.":   "XLY",
    "Consumer Staples": "XLP",
    "Industrials":      "XLI",
    "Utilities":        "XLU",
    "Real Estate":      "XLRE",
    "Materials":        "XLB",
    "Comm. Services":   "XLC",
}

FRED_SERIES = {
    "CPI":                ("CPIAUCSL",  "CPI – All Urban Consumers",   "%"),
    "Core CPI":           ("CPILFESL",  "Core CPI (ex Food & Energy)", "%"),
    "PCE":                ("PCEPI",     "PCE Price Index",              "%"),
    "Core PCE":           ("PCEPILFE",  "Core PCE",                     "%"),
    "Unemployment":       ("UNRATE",    "Unemployment Rate",            "%"),
    "Real GDP":           ("GDPC1",     "Real GDP (2017 $B)",           "B"),
    "Retail Sales":       ("RSAFS",     "Advance Retail Sales",         "M$"),
    "Consumer Sentiment": ("UMCSENT",   "U Mich Consumer Sentiment",    "Idx"),
    "Fed Funds Rate":     ("FEDFUNDS",  "Federal Funds Rate",           "%"),
    "10Y Treasury":       ("DGS10",     "10-Year Treasury Yield",       "%"),
    "2Y Treasury":        ("DGS2",      "2-Year Treasury Yield",        "%"),
}

FRED_NOTES = {
    "CPI":                "Rising CPI pressures the Fed toward higher rates.",
    "Core CPI":           "Strips food & energy — a key short-term Fed signal.",
    "PCE":                "Fed's preferred inflation gauge. Persistent >2% complicates rate cuts.",
    "Core PCE":           "The Fed's primary 2% inflation target.",
    "Unemployment":       "Below ~4% signals a tight labor market that can sustain inflation.",
    "Real GDP":           "Inflation-adjusted output. Declining GDP signals recession risk.",
    "Retail Sales":       "Consumer spending (~70% of GDP) — key economic health indicator.",
    "Consumer Sentiment": "Weak sentiment often precedes consumer spending pullbacks.",
    "Fed Funds Rate":     "Overnight rate set by FOMC — drives all borrowing costs.",
    "10Y Treasury":       "Benchmark long rate affecting mortgages, loans & equity valuations.",
    "2Y Treasury":        "Closely tracks near-term Fed policy expectations.",
}

NEWS_FEEDS = [
    {"name": "Reuters",       "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "Yahoo Finance",  "url": "https://finance.yahoo.com/news/rssindex"},
    {"name": "AP Business",   "url": "https://feeds.apnews.com/rss/business"},
    {"name": "MarketWatch",   "url": "https://feeds.content.dowjones.io/public/rss/mw_bulletins"},
    {"name": "CNBC",          "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
]

NEWS_KEYWORDS = {
    "Federal Reserve": ["fed", "federal reserve", "fomc", "powell", "rate cut",
                        "rate hike", "interest rate", "monetary policy", "basis points"],
    "Inflation":       ["inflation", "cpi", "pce", "core pce", "price index",
                        "consumer prices", "producer prices", "ppi"],
    "Earnings":        ["earnings", "revenue", "eps", "quarterly results", "profit",
                        "guidance", "beats", "misses"],
    "Geopolitics":     ["tariff", "trade war", "sanctions", "china", "russia",
                        "ukraine", "geopolit", "opec", "oil"],
    "Economic Data":   ["gdp", "jobs report", "unemployment", "payrolls",
                        "retail sales", "consumer sentiment", "ism", "pmi"],
    "Sector News":     ["tech", "banks", "healthcare", "energy sector", "real estate",
                        "semiconductor", "pharma", "biotech"],
}

INDEX_INFO = {
    "S&P 500": {
        "full_name": "S&P 500 (Standard & Poor's 500)",
        "what": "A market-cap-weighted index of the 500 largest publicly traded U.S. companies.",
        "composition": "Covers ~80% of total U.S. stock market value. Top holdings include Apple, Microsoft, Nvidia, Amazon, and Alphabet.",
        "why_matters": "The single most-watched benchmark for U.S. equity performance. When investors say 'the market', they almost always mean the S&P 500.",
        "ticker": "^GSPC",
    },
    "Nasdaq": {
        "full_name": "Nasdaq Composite Index",
        "what": "A market-cap-weighted index of all ~3,000+ stocks listed on the Nasdaq exchange.",
        "composition": "Heavily weighted toward technology and growth companies. Apple, Microsoft, Nvidia, Amazon, Meta make up a significant share.",
        "why_matters": "The go-to barometer for tech and growth stock performance. Typically more volatile than the S&P 500.",
        "ticker": "^IXIC",
    },
    "Dow Jones": {
        "full_name": "Dow Jones Industrial Average (DJIA)",
        "what": "A price-weighted index of 30 large, blue-chip U.S. companies selected by the editors of The Wall Street Journal.",
        "composition": "Includes stalwarts like UnitedHealth, Goldman Sachs, Microsoft, Boeing, and McDonald's. Less tech-heavy than the S&P 500.",
        "why_matters": "The oldest and most widely recognized U.S. stock index. A proxy for the health of large-cap, value-oriented American business.",
        "ticker": "^DJI",
    },
    "Russell 2000": {
        "full_name": "Russell 2000 Index",
        "what": "A market-cap-weighted index of the 2,000 smallest companies in the Russell 3000 universe.",
        "composition": "Small-cap U.S. companies across all sectors. More domestically focused than the S&P 500 — less international revenue exposure.",
        "why_matters": "A key gauge of small-cap and domestic economic health. Often leads the broader market at turning points. More sensitive to interest rates and credit conditions.",
        "ticker": "^RUT",
    },
    "VIX": {
        "full_name": "CBOE Volatility Index ('The Fear Gauge')",
        "what": "Measures the market's expectation of 30-day S&P 500 volatility, derived from options prices.",
        "composition": "Not a stock index — it's a real-time volatility measure. Below 15 = calm. 15–25 = normal. Above 25 = elevated fear. Above 40 = panic.",
        "why_matters": "When VIX spikes, investors are paying up for downside protection — a signal of fear and uncertainty. Low VIX = complacency. High VIX = potential buying opportunity if fundamentals are intact.",
        "ticker": "^VIX",
    },
    "Dev. Markets": {
        "full_name": "iShares MSCI EAFE ETF (EFA) — Developed Markets Proxy",
        "what": "Tracks the MSCI EAFE Index, covering large- and mid-cap equities in 21 developed market countries excluding the U.S. and Canada.",
        "composition": "Europe (~60%), Japan (~25%), Australia/Pacific (~15%). Top countries: Japan, UK, France, Switzerland, Germany.",
        "why_matters": "Provides international diversification. Sensitive to USD strength (a stronger dollar hurts returns for U.S. investors), European growth, and global trade conditions.",
        "ticker": "EFA",
    },
    "Emg. Markets": {
        "full_name": "iShares MSCI Emerging Markets ETF (EEM) — Emerging Markets Proxy",
        "what": "Tracks the MSCI Emerging Markets Index, covering large- and mid-cap equities across 24 developing economies.",
        "composition": "China (~25%), India (~20%), Taiwan, South Korea, Brazil, South Africa. High exposure to commodities and consumer growth themes.",
        "why_matters": "Higher risk, higher potential return. Sensitive to USD strength, commodity prices, China policy, and global risk appetite. Often the first to sell off in risk-off environments.",
        "ticker": "EEM",
    },
}

FRED_INFO = {
    "CPI": {
        "full_name": "Consumer Price Index for All Urban Consumers (CPI-U)",
        "what": "Measures the average change in prices paid by urban consumers for a basket of goods and services including food, housing, clothing, transportation, and medical care.",
        "why_matters": "The most widely cited inflation measure. When CPI rises faster than the Fed's ~2% target, the Fed tends to raise interest rates — which pressures equity valuations and borrowing costs.",
        "source": "Bureau of Labor Statistics (BLS), released monthly.",
    },
    "Core CPI": {
        "full_name": "Core CPI (excluding Food & Energy)",
        "what": "Same as CPI but strips out volatile food and energy prices to reveal the underlying inflation trend.",
        "why_matters": "The Fed watches Core CPI more closely than headline CPI because food and energy prices swing wildly. A persistently high Core CPI signals structural inflation that requires policy action.",
        "source": "Bureau of Labor Statistics (BLS), released monthly.",
    },
    "PCE": {
        "full_name": "Personal Consumption Expenditures Price Index",
        "what": "Measures price changes in consumer spending across all goods and services, using a broader and more flexible basket than CPI.",
        "why_matters": "The Fed's officially preferred inflation gauge — it adjusts for consumer substitution behavior (e.g. switching from beef to chicken when beef prices rise), making it more accurate than CPI.",
        "source": "Bureau of Economic Analysis (BEA), released monthly.",
    },
    "Core PCE": {
        "full_name": "Core PCE Price Index (excluding Food & Energy)",
        "what": "PCE stripped of food and energy — the Fed's single most important inflation metric.",
        "why_matters": "The Federal Reserve's explicit 2% inflation target is measured against Core PCE. If this number stays above 2%, rate cuts are unlikely. Below 2% for sustained periods opens the door to easing.",
        "source": "Bureau of Economic Analysis (BEA), released monthly.",
    },
    "Unemployment": {
        "full_name": "U.S. Unemployment Rate (U-3)",
        "what": "The percentage of the labor force that is jobless and actively seeking employment.",
        "why_matters": "One half of the Fed's dual mandate (along with price stability). A very low unemployment rate signals a tight labor market that can sustain wage growth and inflation — making the Fed less likely to cut rates.",
        "source": "Bureau of Labor Statistics (BLS), released monthly in the Jobs Report.",
    },
    "Real GDP": {
        "full_name": "Real Gross Domestic Product (inflation-adjusted)",
        "what": "The total value of all goods and services produced in the U.S., adjusted for inflation. Measured in chained 2017 dollars.",
        "why_matters": "The broadest measure of economic health. Two consecutive quarters of declining GDP = technical recession. Strong GDP growth supports corporate earnings; weak GDP signals contraction risk.",
        "source": "Bureau of Economic Analysis (BEA), released quarterly (advance, revised, final estimates).",
    },
    "Retail Sales": {
        "full_name": "Advance Monthly Retail Trade Survey",
        "what": "Measures total receipts of retail stores in the U.S., a leading indicator of consumer spending.",
        "why_matters": "Consumer spending drives ~70% of U.S. GDP. Strong retail sales = healthy consumer; weak sales signal economic slowdown. A key input for Fed policy and earnings forecasts.",
        "source": "U.S. Census Bureau, released monthly.",
    },
    "Consumer Sentiment": {
        "full_name": "University of Michigan Consumer Sentiment Index",
        "what": "A monthly survey measuring consumer confidence about personal finances and the broader economy.",
        "why_matters": "A leading indicator — how consumers feel today predicts how they'll spend tomorrow. Collapsing sentiment often precedes spending pullbacks and economic slowdowns even before the data shows it.",
        "source": "University of Michigan Survey Research Center, released monthly (preliminary and final).",
    },
    "Fed Funds Rate": {
        "full_name": "Federal Funds Effective Rate",
        "what": "The interest rate at which banks lend reserve balances to other banks overnight. Set by the Federal Open Market Committee (FOMC).",
        "why_matters": "The most important interest rate in the world. It's the anchor for all other borrowing costs — mortgages, credit cards, corporate loans, and more. Raising rates slows inflation but can slow the economy; cutting rates stimulates growth but can stoke inflation.",
        "source": "Federal Reserve, adjusted at scheduled FOMC meetings (8 per year).",
    },
    "10Y Treasury": {
        "full_name": "10-Year U.S. Treasury Note Yield",
        "what": "The annualized return on a U.S. government bond maturing in 10 years. Considered the 'risk-free' benchmark rate.",
        "why_matters": "The single most important rate in global finance. It drives mortgage rates, corporate borrowing costs, and is used to discount future earnings — making it the primary driver of equity valuations. Rising yields = pressure on stock multiples.",
        "source": "U.S. Department of Treasury, updated daily.",
    },
    "2Y Treasury": {
        "full_name": "2-Year U.S. Treasury Note Yield",
        "what": "The annualized return on a U.S. government bond maturing in 2 years.",
        "why_matters": "The 2-year yield is extremely sensitive to near-term Fed policy expectations — it essentially prices in what the market thinks the Fed will do over the next 2 years. When 2Y > 10Y (inverted yield curve), it has historically preceded recessions.",
        "source": "U.S. Department of Treasury, updated daily.",
    },
    "Fed Funds": {
        "full_name": "Federal Funds Effective Rate",
        "what": "The interest rate at which banks lend reserve balances to other banks overnight.",
        "why_matters": "The anchor for all borrowing costs in the economy. Set by the FOMC 8 times per year.",
        "source": "Federal Reserve.",
    },
    "2Y Yield": {
        "full_name": "2-Year U.S. Treasury Yield",
        "what": "Return on a 2-year U.S. government bond — highly sensitive to near-term Fed rate expectations.",
        "why_matters": "When 2Y yield rises above 10Y yield, the curve inverts — historically a recession warning signal.",
        "source": "U.S. Treasury, daily.",
    },
    "10Y Yield": {
        "full_name": "10-Year U.S. Treasury Yield",
        "what": "The benchmark long-term risk-free rate that anchors mortgage rates, corporate borrowing, and equity valuations.",
        "why_matters": "Rising 10Y yields compress equity multiples and increase borrowing costs across the economy.",
        "source": "U.S. Treasury, daily.",
    },
}

# ── Upcoming events: edit this list each week ─────────────────────────────────
def upcoming_events():
    return [
        {"date": "Jul 8,  2026", "event": "JOLTS Job Openings (May)",             "cat": "Jobs"},
        {"date": "Jul 10, 2026", "event": "CPI Release (June)",                   "cat": "Inflation"},
        {"date": "Jul 10, 2026", "event": "Initial Jobless Claims",                "cat": "Jobs"},
        {"date": "Jul 11, 2026", "event": "PPI Release (June)",                    "cat": "Inflation"},
        {"date": "Jul 11, 2026", "event": "U Mich Consumer Sentiment (prelim)",    "cat": "Economic Data"},
        {"date": "Jul 15, 2026", "event": "Retail Sales (June)",                   "cat": "Economic Data"},
        {"date": "Jul 16, 2026", "event": "Housing Starts & Building Permits",     "cat": "Economic Data"},
        {"date": "Jul 25, 2026", "event": "PCE Inflation (June)",                  "cat": "Inflation"},
        {"date": "Jul 25, 2026", "event": "Real GDP Advance Estimate Q2 2026",     "cat": "GDP"},
        {"date": "Jul 28, 2026", "event": "FOMC Meeting Day 1",                    "cat": "Fed"},
        {"date": "Jul 29, 2026", "event": "FOMC Rate Decision & Press Conference", "cat": "Fed"},
        {"date": "Aug 7,  2026", "event": "Jobs Report (July)",                    "cat": "Jobs"},
        {"date": "Aug 7,  2026", "event": "ISM Manufacturing PMI",                 "cat": "Economic Data"},
    ]

# ═════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ═════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)
def get_prices(ticker: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period="1y", progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        return df
    except Exception:
        return pd.DataFrame()


def price_stats(df: pd.DataFrame, week_end: date) -> dict:
    if df.empty or "Close" not in df.columns:
        return {}
    idx = df.index
    ts  = pd.Timestamp(week_end)
    sub = df[idx.normalize() <= ts]
    if sub.empty:
        return {}
    cur = float(sub["Close"].iloc[-1])
    d   = sub.index[-1].date()

    def lookback(days):
        t = ts - pd.Timedelta(days=days)
        s = df[idx.normalize() <= t]
        return float(s["Close"].iloc[-1]) if not s.empty else None

    def pct(new, old):
        if new is None or old is None or old == 0:
            return None
        return round((new - old) / old * 100, 2)

    ytd = df[idx.year == ts.year]
    return {
        "current":   round(cur, 2),
        "date":      d,
        "week_chg":  pct(cur, lookback(7)),
        "month_chg": pct(cur, lookback(30)),
        "ytd_chg":   pct(cur, float(ytd["Close"].iloc[0]) if not ytd.empty else None),
        "high_52":   round(float(df["High"].tail(252).max()), 2),
        "low_52":    round(float(df["Low"].tail(252).min()), 2),
        "series":    sub["Close"].tail(7),   # 5–7 trading days = 1 week to match 1W % shown
    }


@st.cache_data(ttl=3600, show_spinner=False)
def get_fred(series_id: str, api_key: str) -> pd.DataFrame:
    if not api_key:
        return pd.DataFrame()
    try:
        url = (
            "https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={api_key}"
            "&file_type=json&sort_order=desc&limit=36"
        )
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()
        obs = r.json().get("observations", [])
        df  = pd.DataFrame(obs)[["date", "value"]]
        df["date"]  = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df.dropna().sort_values("date").reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def get_news() -> list:
    articles = []
    for feed in NEWS_FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            for e in parsed.entries[:12]:
                title   = getattr(e, "title", "")
                summary = getattr(e, "summary", getattr(e, "description", ""))[:300]
                link    = getattr(e, "link", "#")
                pub     = getattr(e, "published", getattr(e, "updated", ""))
                try:
                    pub_str = pd.to_datetime(pub, utc=True)\
                                .tz_convert("America/New_York")\
                                .strftime("%b %d %Y  %I:%M %p ET")
                except Exception:
                    pub_str = str(pub)[:25]
                text = (title + " " + summary).lower()
                cat  = "Market News"
                for c, kws in NEWS_KEYWORDS.items():
                    if any(k in text for k in kws):
                        cat = c
                        break
                # Strip all HTML tags at fetch time so rendering is always clean
                clean_title   = re.sub(r'<[^>]+>', '', title).strip()
                clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                articles.append({"title": clean_title, "summary": clean_summary,
                                  "link": link, "source": feed["name"],
                                  "pub": pub_str, "category": cat})
        except Exception:
            continue
    seen, out = set(), []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            out.append(a)
    return out

# ═════════════════════════════════════════════════════════════════════════════
# CHARTS  – each function builds its own layout from scratch (no **BASE_LAYOUT)
# ═════════════════════════════════════════════════════════════════════════════

def _base(fig, height, margin, extra=None):
    """Apply common dark-theme layout to any figure."""
    kwargs = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE, family="Inter, Segoe UI, sans-serif", size=11),
        height=height,
        margin=margin,
        hovermode="x unified",
        xaxis=dict(showgrid=False, color=SILVER, tickfont=dict(size=9)),
        yaxis=dict(gridcolor=SLATE, color=SILVER, tickfont=dict(size=9)),
    )
    if extra:
        kwargs.update(extra)
    fig.update_layout(**kwargs)
    return fig


def sparkline(series: pd.Series, color: str = GREEN) -> go.Figure:
    vals = series.values
    if len(vals) < 2:
        return go.Figure()
    # Zoom y-axis to the actual price range so small moves look dramatic
    mn, mx = vals.min(), vals.max()
    padding = (mx - mn) * 0.15 if mx != mn else abs(mn) * 0.01
    fig = go.Figure(go.Scatter(
        x=series.index, y=vals,
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=hex_rgba(color, 0.08),
        hovertemplate="%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=75,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, range=[mn - padding, mx + padding]),
    )
    return fig


def sector_chart(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("Week %")
    colors = [GREEN if v >= 0 else RED for v in df["Week %"]]
    # Place labels inside bars for negative values, outside for positive
    positions = ["outside" if v >= 0 else "inside" for v in df["Week %"]]
    fig = go.Figure(go.Bar(
        x=df["Week %"], y=df["Sector"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in df["Week %"]],
        textposition=positions,
        textfont=dict(color=WHITE, size=10),
        hovertemplate="%{y}: %{x:+.2f}%<extra></extra>",
        cliponaxis=False,
    ))
    return _base(fig, height=560,
                 margin=dict(l=130, r=100, t=10, b=10),
                 extra=dict(
                     showlegend=False,
                     hovermode="closest",
                     xaxis=dict(ticksuffix="%", showgrid=True, gridcolor=SLATE,
                                zeroline=True, zerolinecolor=SILVER, zerolinewidth=1,
                                color=SILVER, tickfont=dict(size=9),
                                automargin=True),
                     yaxis=dict(showgrid=False, color=WHITE, tickfont=dict(size=10),
                                automargin=True),
                 ))


def yield_chart(df2: pd.DataFrame, df10: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not df2.empty:
        fig.add_trace(go.Scatter(
            x=df2["date"].tail(252), y=df2["value"].tail(252),
            name="2Y", line=dict(color=GOLD, width=1.8),
            hovertemplate="2Y: %{y:.2f}%<extra></extra>",
        ))
    if not df10.empty:
        fig.add_trace(go.Scatter(
            x=df10["date"].tail(252), y=df10["value"].tail(252),
            name="10Y", line=dict(color=BLUE, width=1.8),
            hovertemplate="10Y: %{y:.2f}%<extra></extra>",
        ))
    return _base(fig, height=240,
                 margin=dict(l=8, r=8, t=30, b=8),
                 extra=dict(
                     yaxis=dict(ticksuffix="%", gridcolor=SLATE, color=SILVER),
                     legend=dict(orientation="h", y=1.06, x=0,
                                 font=dict(size=10, color=WHITE)),
                 ))


def fred_chart(df: pd.DataFrame, color: str = GOLD) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=df["date"].tail(36), y=df["value"].tail(36),
        mode="lines+markers",
        line=dict(color=color, width=1.6),
        marker=dict(size=3, color=color),
        hovertemplate="%{x|%b %Y}: %{y:,.2f}<extra></extra>",
    ))
    return _base(fig, height=130,
                 margin=dict(l=4, r=4, t=6, b=4),
                 extra=dict(showlegend=False))

# ═════════════════════════════════════════════════════════════════════════════
# UI HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def section(title: str):
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)


def delta_span(val, invert=False):
    if val is None:
        return '<span class="neu">N/A</span>'
    pos = (val >= 0) if not invert else (val < 0)
    cls = "up" if pos else "dn"
    arrow = "▲" if val >= 0 else "▼"
    return f'<span class="{cls}">{arrow} {abs(val):.2f}%</span>'


def card(label, value, delta="", sub=""):
    st.markdown(f"""
    <div class="card">
        <div class="card-label">{label}</div>
        <div class="card-value">{value}</div>
        {f'<div style="margin-top:3px">{delta}</div>' if delta else ""}
        {f'<div style="color:{SILVER};font-size:10px;margin-top:2px">{sub}</div>' if sub else ""}
    </div>""", unsafe_allow_html=True)


def cat_color(cat):
    return {"Fed": BLUE, "Inflation": RED, "Jobs": GREEN,
            "GDP": GOLD, "Economic Data": SILVER}.get(cat, SILVER)

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(f"""
    <div style="padding:10px 0 18px">
        <div style="font-size:17px;font-weight:800;color:{GOLD}">📈 MARKET PULSE</div>
        <div style="font-size:9px;color:{SILVER};letter-spacing:0.12em;
                    text-transform:uppercase;margin-top:2px">Weekly Update Dashboard</div>
    </div>""", unsafe_allow_html=True)

    today = date.today()
    fred_key = "74a9d84ec1a939095574b903b2a44449"
    anthropic_key = "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"

    # Week mode: live or historical
    if "week_mode" not in st.session_state:
        st.session_state["week_mode"] = "live"
    if "historical_date" not in st.session_state:
        st.session_state["historical_date"] = today

    mode = st.session_state["week_mode"]
    week_end = today if mode == "live" else st.session_state["historical_date"]

    st.markdown(f"""
    <div style="margin-top:16px;padding:10px;background:{NAVY};border-radius:6px;
                font-size:10px;color:{TEXT};line-height:1.8">
        <b style="color:{GOLD}">Data Sources</b><br>
        ✅ Indexes / ETFs: yfinance<br>
        {'✅' if fred_key else '⚠️'} Economic: FRED API<br>
        ✅ News: RSS feeds<br>
        📅 Events: manually edited<br><br>
        <b style="color:{GOLD}">Refreshed:</b><br>
        {datetime.now().strftime('%b %d %Y  %H:%M')}
    </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ═════════════════════════════════════════════════════════════════════════════

# Runtime button style injection — overrides Streamlit's late-loading CSS
# Name is hardcoded in CSS body::after — cannot be removed without editing CSS
st.markdown(f"""
<style>
button, .stButton > button, button[kind] {{
    background-color: {CARD} !important;
    color: {GOLD} !important;
    border: 1px solid {SLATE} !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}}
button:hover, .stButton > button:hover, button[kind]:hover {{
    background-color: {SLATE} !important;
    border-color: {GOLD} !important;
    color: {WHITE} !important;
    box-shadow: none !important;
}}
[data-testid="stHorizontalBlock"] > div,
[data-testid="column"] {{
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    box-shadow: none !important;
}}


</style>""", unsafe_allow_html=True)

# Watermark injected as a separate st.markdown at the very top level
# Uses html::after which sits above ALL Streamlit containers
st.markdown("""
<style>
html::after {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    z-index: 2147483647;
    background: transparent;
}
</style>
<div style="
    position: fixed;
    top: 10px;
    right: 18px;
    z-index: 2147483647;
    text-align: right;
    pointer-events: none;
    font-family: Inter, Segoe UI, sans-serif;
    transform: translateZ(0);
    will-change: transform;
">
    <div style="font-size:11px;font-weight:700;color:#C8A96E;letter-spacing:0.06em;line-height:1.5">Built by Emmitt Macor</div>
</div>""", unsafe_allow_html=True)

# ── Week Mode Banner ─────────────────────────────────────────────────────────
is_live = st.session_state.get("week_mode", "live") == "live"

# Top bar
hcol1, hcol2, hcol3 = st.columns([6, 2, 0.7])

with hcol1:
    mode_label = f"Live · {today.strftime('%B %d, %Y')}" if is_live else f"Historical · Week of {week_end.strftime('%B %d, %Y')}"
    border_color = GREEN if is_live else GOLD
    st.markdown(f"""
    <div style="padding:6px 0 4px;border-bottom:1px solid {SLATE};margin-bottom:4px">
        <span style="font-size:20px;font-weight:800;color:{WHITE}">
            Bridgeway Weekly Market Update
        </span>
        <span style="font-size:11px;font-weight:600;color:{border_color};margin-left:12px;
                     background:{'rgba(31,173,106,0.12)' if is_live else 'rgba(200,169,110,0.12)'};
                     padding:3px 10px;border-radius:20px;border:1px solid {border_color}">
            {'🟢 LIVE' if is_live else '📅 HISTORICAL'}
        </span>
        <span style="font-size:11px;color:{SILVER};margin-left:10px">{mode_label}</span>
        <span style="font-size:10px;color:{SILVER};margin-left:16px">{datetime.now().strftime('%H:%M ET')}</span>
    </div>""", unsafe_allow_html=True)

with hcol2:
    if is_live:
        p1, p2 = st.columns([2, 1])
        with p1:
            sel_date = st.date_input(
                "v",
                value=today - timedelta(days=7),
                max_value=today,
                label_visibility="collapsed",
                key="hist_date_picker",
            )
        with p2:
            if st.button("📅 View", use_container_width=True, key="go_historical"):
                st.session_state["week_mode"] = "historical"
                st.session_state["historical_date"] = sel_date
                st.cache_data.clear()
                st.rerun()
    else:
        if st.button(f"🟢 Back to Live", use_container_width=True, key="go_live"):
            st.session_state["week_mode"] = "live"
            st.cache_data.clear()
            st.rerun()

with hcol3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Historical mode warning banner
if not is_live:
    st.markdown(f"""
    <div style="background:rgba(200,169,110,0.08);border:1px solid {GOLD};border-radius:6px;
                padding:8px 16px;margin-bottom:8px;font-size:12px;color:{GOLD}">
        📅 <b>Historical Mode</b> — Showing market data for the week ending
        <b>{week_end.strftime('%B %d, %Y')}</b>.
        Click <b>🟢 Back to Live</b> to return to current market data.
    </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═════════════════════════════════════════════════════════════════════════════

with st.spinner("Loading market data…"):
    idx_dfs   = {n: get_prices(t) for n, t in INDEX_TICKERS.items()}
    idx_stats = {n: price_stats(df, week_end)
                 for n, df in idx_dfs.items() if not df.empty}

    sec_dfs   = {n: get_prices(t) for n, t in SECTOR_TICKERS.items()}
    sec_stats = {n: price_stats(df, week_end)
                 for n, df in sec_dfs.items() if not df.empty}

    fred = {}
    if fred_key:
        for label, (sid, _, _) in FRED_SERIES.items():
            fred[label] = get_fred(sid, fred_key)

    news = get_news()

# ═════════════════════════════════════════════════════════════════════════════
# 1 · EXECUTIVE SUMMARY  (AI-powered)
# ═════════════════════════════════════════════════════════════════════════════

section("01 · Executive Summary")

def build_market_context() -> str:
    """Assemble a structured market snapshot string to feed into the AI prompt."""
    lines = []

    # Index performance
    lines.append("=== INDEX PERFORMANCE (week-over-week) ===")
    for name, s in idx_stats.items():
        wk = s.get("week_chg")
        lines.append(f"  {name}: {s['current']:,.2f}  |  1W: {wk:+.2f}%" if wk is not None
                     else f"  {name}: {s['current']:,.2f}  |  1W: N/A")

    # Sector performance
    lines.append("\n=== SECTOR PERFORMANCE (week-over-week) ===")
    for name, s in sec_stats.items():
        wk = s.get("week_chg")
        lines.append(f"  {name}: {wk:+.2f}%" if wk is not None else f"  {name}: N/A")

    # Top news headlines
    lines.append("\n=== TOP NEWS HEADLINES THIS WEEK ===")
    for a in news[:20]:
        lines.append(f"  [{a['category']}] {a['title']}")

    return "\n".join(lines)


def build_market_snapshot() -> str:
    """Build a structured text snapshot of all live market data for AI context."""
    sp  = idx_stats.get("S&P 500", {})
    nq  = idx_stats.get("Nasdaq", {})
    dj  = idx_stats.get("Dow Jones", {})
    ru  = idx_stats.get("Russell 2000", {})
    vix = idx_stats.get("VIX", {})

    ranked_s = sorted(
        [(k, v["week_chg"]) for k, v in sec_stats.items() if v.get("week_chg") is not None],
        key=lambda x: x[1]
    )
    sec_lines = "\n".join(f"  {k}: {v:+.2f}%" for k, v in ranked_s)
    news_lines = "\n".join(f"  [{a['category']}] {a['title']}" for a in news[:12]) if news else "  None"
    fred_lines = ""
    for lbl, df_f in fred.items():
        if not df_f.empty:
            fred_lines += f"  {lbl}: {df_f['value'].iloc[-1]:.2f} ({df_f['date'].iloc[-1].strftime('%b %Y')})\n"

    return f"""Week ending {week_end.strftime('%B %d, %Y')}

INDEXES (1W change):
  S&P 500: {sp.get('current','N/A')} ({f"{sp.get('week_chg',0):+.2f}%"}) | 1M: {f"{sp.get('month_chg',0):+.2f}%"} | YTD: {f"{sp.get('ytd_chg',0):+.2f}%"}
  Nasdaq:  {nq.get('current','N/A')} ({f"{nq.get('week_chg',0):+.2f}%"})
  Dow:     {dj.get('current','N/A')} ({f"{dj.get('week_chg',0):+.2f}%"})
  Russell: {ru.get('current','N/A')} ({f"{ru.get('week_chg',0):+.2f}%"})
  VIX:     {vix.get('current','N/A')} ({f"{vix.get('week_chg',0):+.2f}%"})

SECTORS (1W, best to worst):
{sec_lines}

ECONOMIC DATA:
{fred_lines if fred_lines else "  FRED not loaded"}

TOP NEWS:
{news_lines}"""


@st.cache_data(ttl=1800, show_spinner=False)
def ai_generate(prompt: str, cache_key: str, api_key: str) -> str:
    """Call Claude API and cache the result for 30 minutes."""
    if not api_key:
        return ""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 800,
                  "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        if r.status_code == 200:
            blocks = r.json().get("content", [])
            return " ".join(b["text"].strip() for b in blocks if b.get("type") == "text" and b.get("text","").strip())
    except Exception:
        pass
    return ""


def generate_rich_summary() -> str:
    """AI-powered executive summary using live data + web search."""
    snapshot = build_market_snapshot()
    prompt = f"""You are a senior equity market strategist writing the weekly executive summary for UBS Wealth Management clients.

Here is the live market data:
{snapshot}

Write exactly 6 bullet points in HTML <li> tags. Each bullet must:
- Start with <b>Section Title:</b>
- Be 2-3 sentences, specific and data-driven
- Cite actual numbers, index names, sector names, news events from the data above
- Explain CAUSE and EFFECT (why did it happen, what does it mean)
- Sound like Goldman Sachs research — no generic filler

Sections:
1. <b>Market Overview:</b> Overall direction, magnitude, risk-on vs risk-off tone
2. <b>Key Drivers:</b> 3-4 specific catalysts from news that moved markets this week with cause-and-effect
3. <b>Index Performance:</b> Leaders and laggards with reasons for divergence
4. <b>Sector Rotation:</b> Top/bottom sectors, what the rotation signals about investor sentiment
5. <b>Volatility & Sentiment:</b> VIX interpretation and institutional risk appetite
6. <b>What to Watch Next Week:</b> 3-4 specific upcoming catalysts and why they matter

Return ONLY the 6 <li> tags, nothing else."""

    result = ai_generate(prompt, f"exec_summary_{week_end}", anthropic_key)

    if result and "<li>" in result:
        return result

    # Fallback — instant static generation
    return _static_summary()


def _static_summary() -> str:
    """Fast static summary — always works instantly."""
    items = []
    sp   = idx_stats.get("S&P 500", {})
    nq   = idx_stats.get("Nasdaq", {})
    dj   = idx_stats.get("Dow Jones", {})
    vix  = idx_stats.get("VIX", {})
    sp_chg  = sp.get("week_chg", 0) or 0
    nq_chg  = nq.get("week_chg", 0) or 0
    dj_chg  = dj.get("week_chg", 0) or 0
    vix_cur = vix.get("current", 0) or 0
    vix_chg = vix.get("week_chg", 0) or 0
    direction = "gained" if sp_chg >= 0 else "declined"
    mag = "modestly" if abs(sp_chg) < 1 else ("sharply" if abs(sp_chg) > 2.5 else "meaningfully")
    tone = "risk-on" if sp_chg >= 0 and vix_cur < 20 else "risk-off"

    div = ""
    if dj_chg > 0 and nq_chg < -1:
        div = f" A notable divergence emerged — the Dow gained {dj_chg:+.2f}% while the Nasdaq fell {nq_chg:+.2f}%, reflecting rotation from growth to value."
    elif nq_chg > dj_chg + 1:
        div = f" Growth outperformed value, with the Nasdaq ({nq_chg:+.2f}%) ahead of the Dow ({dj_chg:+.2f}%)."

    items.append(f"<b>Market Overview:</b> U.S. equities {mag} {direction} in a {tone} week ending {week_end.strftime('%B %d, %Y')}. The S&P 500 moved {sp_chg:+.2f}% while the Nasdaq changed {nq_chg:+.2f}%.{div}")

    top_news = [a for a in news[:20] if a["category"] in ("Federal Reserve","Inflation","Earnings","Geopolitics","Economic Data")][:3]
    if top_news:
        drivers = "; ".join(f'"{a["title"][:60]}…" ({a["source"]})' for a in top_news)
        items.append(f"<b>Key Drivers:</b> Key catalysts this week included: {drivers}. These developments shaped sector leadership and index direction.")

    ranked_i = sorted([(k, v["week_chg"]) for k, v in idx_stats.items() if v.get("week_chg") is not None], key=lambda x: x[1])
    if len(ranked_i) >= 2:
        bi, bv = ranked_i[-1]; wi, wv = ranked_i[0]
        items.append(f"<b>Index Performance:</b> {bi} led major indexes ({bv:+.2f}%) while {wi} underperformed ({wv:+.2f}%). Divergence reflects differing sensitivity to this week's macro and sector themes.")

    ranked_s = sorted([(k, v["week_chg"]) for k, v in sec_stats.items() if v.get("week_chg") is not None], key=lambda x: x[1])
    if len(ranked_s) >= 2:
        bs, bsv = ranked_s[-1]; ws, wsv = ranked_s[0]
        defensive = {"Healthcare","Utilities","Consumer Staples"}
        signal = "classic defensive rotation — consistent with risk-aversion" if bs in defensive and sp_chg < 0 else "cyclical leadership — consistent with improving risk appetite" if bs not in defensive and sp_chg > 0 else "mixed rotation"
        items.append(f"<b>Sector Rotation:</b> {bs} led ({bsv:+.2f}%) while {ws} lagged ({wsv:+.2f}%). This pattern is consistent with a {signal}.")

    regime = "low — suggesting complacency" if vix_cur < 15 else ("elevated — signaling active hedging demand" if vix_cur > 25 else "moderate — consistent with orderly price discovery")
    move = "surged" if vix_chg > 5 else ("rose" if vix_chg > 0 else "fell")
    items.append(f"<b>Volatility & Sentiment:</b> The VIX {move} to {vix_cur:.1f} ({vix_chg:+.1f}% on week), a level indicative of {regime}. {'Rising volatility amplifies the risk-off signal and suggests institutions are buying downside protection.' if vix_chg > 3 else 'Stable volatility suggests markets are digesting crosscurrents without panic.'}")

    ev = upcoming_events()[:3]
    if ev:
        watch = "; ".join(f"{e['event']} ({e['date']})" for e in ev)
        items.append(f"<b>What to Watch Next Week:</b> Key upcoming catalysts include: {watch}. Any surprise in inflation or employment data could meaningfully reprice rate expectations and equity valuations.")
    else:
        items.append("<b>What to Watch Next Week:</b> Monitor CPI, PCE, the jobs report, and any Federal Reserve communications for signals on the near-term rate path.")

    return "".join(f"<li style='margin-bottom:10px'>{i}</li>" for i in items)


def generate_daily_summary() -> str:
    """AI-powered DAILY update — what's happening in the market today (web search)."""
    snapshot = build_market_snapshot()
    today_label = date.today().strftime("%B %d, %Y")
    prompt = f"""You are a senior market strategist writing a brief DAILY market update for {today_label} for UBS Wealth Management clients. Use web search to find what is happening in U.S. markets TODAY ({today_label}) — intraday index direction, the single biggest market-moving story, a standout mover, and the next catalyst traders are watching.

For background context only (this is weekly data, NOT today's intraday action):
{snapshot}

Write exactly 4 short bullet points in HTML <li> tags. Each bullet must:
- Start with <b>Label:</b>
- Be ONE concise, skimmable sentence (roughly 12-22 words)
- Reference today's specific moves, levels, or news wherever available

Use these labels, in this order:
1. <b>Today's Tape:</b> direction of the major indexes today and the overall tone (risk-on / risk-off)
2. <b>Driving It:</b> the single biggest catalyst moving markets today
3. <b>Notable Mover:</b> a standout stock, sector, or asset today and why
4. <b>On Deck:</b> the next data release, earnings, or Fed event traders are watching today or tomorrow

Return ONLY the 4 <li> tags, nothing else."""

    result = ai_generate(prompt, f"daily_summary_{date.today()}", anthropic_key)
    if result and "<li>" in result:
        return result
    return _static_daily_summary()


def _static_daily_summary() -> str:
    """Fast static daily fallback — uses the freshest available data and headlines."""
    items = []
    sp  = idx_stats.get("S&P 500", {})
    nq  = idx_stats.get("Nasdaq", {})
    vix = idx_stats.get("VIX", {})
    today_label = date.today().strftime("%B %d, %Y")
    items.append(
        f"<b>Latest Levels:</b> S&P 500 at {sp.get('current','N/A')}, "
        f"Nasdaq at {nq.get('current','N/A')}, VIX at {vix.get('current','N/A')} "
        f"as of the most recent reading on {today_label}.")
    fresh = news[:3]
    if fresh:
        for a in fresh:
            items.append(f"<b>{a['category']}:</b> {a['title']}")
    else:
        items.append("<b>Headlines:</b> Live news feed temporarily unavailable — check back shortly.")
    return "".join(f"<li style='margin-bottom:8px'>{i}</li>" for i in items)


# Build and render the summary — static version shown instantly, then upgraded by AI
week_str = week_end.strftime("%B %d, %Y")
today_label = date.today().strftime("%B %d, %Y")

# ── DAILY UPDATE (today's market action) ──────────────────────────────────────
st.markdown(
    f'<div style="font-size:11px;font-weight:700;letter-spacing:0.12em;'
    f'text-transform:uppercase;color:{GOLD};margin:2px 0 8px 0">'
    f'Daily Update · {today_label}</div>',
    unsafe_allow_html=True)

daily_placeholder = st.empty()
daily_placeholder.markdown(
    f'<div class="sbox" style="min-height:60px">'
    f'<div style="color:{SILVER};font-size:12px;font-style:italic">Fetching today\'s market action…</div>'
    f'</div>',
    unsafe_allow_html=True)

with st.spinner(""):
    daily_html = generate_daily_summary()

if daily_html:
    daily_html = re.sub(r'```[\w]*\n?', '', daily_html).strip()
    daily_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', daily_html)

if daily_html and "<li>" in daily_html:
    daily_placeholder.markdown(
        f'<div class="sbox"><ul style="margin:0;padding-left:18px">{daily_html}</ul></div>',
        unsafe_allow_html=True)
else:
    daily_placeholder.markdown(
        f'<div class="sbox"><ul style="margin:0;padding-left:18px">{_static_daily_summary()}</ul></div>',
        unsafe_allow_html=True)

# ── WEEKLY SUMMARY ────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="font-size:11px;font-weight:700;letter-spacing:0.12em;'
    f'text-transform:uppercase;color:{GOLD};margin:20px 0 8px 0">'
    f'Weekly Summary · Week of {week_str}</div>',
    unsafe_allow_html=True)

static_html = _static_summary()  # used for AI chat context only
summary_placeholder = st.empty()

# Show empty box with loading indicator first
summary_placeholder.markdown(
    f'<div class="sbox" style="min-height:80px">'
    f'<div style="color:{SILVER};font-size:12px;font-style:italic">Generating weekly market analysis…</div>'
    f'</div>',
    unsafe_allow_html=True
)

# Auto-generate AI summary
with st.spinner(""):
    ai_html = generate_rich_summary()

# Clean up any markdown artifacts the AI may return (```html blocks etc)
import re as _re
if ai_html:
    ai_html = _re.sub(r'```[\w]*\n?', '', ai_html).strip()
    ai_html = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', ai_html)

# Ensure "What to Watch" bullet is always present
if ai_html and "<li>" in ai_html:
    if "What to Watch" not in ai_html:
        ev = upcoming_events()[:3]
        watch_str = "; ".join(f"{e['event']} ({e['date']})" for e in ev) if ev else "CPI, PCE, jobs report, and Fed communications"
        ai_html += f"<li style='margin-bottom:10px'><b>What to Watch Next Week:</b> Key catalysts include: {watch_str}. Monitor these closely as they will directly shape near-term rate expectations and equity direction.</li>"

    summary_placeholder.markdown(
        f'<div class="sbox"><ul style="margin:0;padding-left:18px">{ai_html}</ul></div>',
        unsafe_allow_html=True
    )
else:
    # Fallback to static if AI fails
    summary_placeholder.markdown(
        f'<div class="sbox"><ul style="margin:0;padding-left:18px">{static_html}</ul></div>',
        unsafe_allow_html=True
    )

# ── AI Market Assistant ───────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Build full dashboard context for AI
_sp  = idx_stats.get("S&P 500", {})
_nq  = idx_stats.get("Nasdaq", {})
_dj  = idx_stats.get("Dow Jones", {})
_ru  = idx_stats.get("Russell 2000", {})
_vix = idx_stats.get("VIX", {})
_efa = idx_stats.get("Dev. Markets", {})
_eem = idx_stats.get("Emg. Markets", {})

_ranked_s = sorted(
    [(k, v["week_chg"]) for k, v in sec_stats.items() if v.get("week_chg") is not None],
    key=lambda x: x[1],
)
_sec_lines = "\n".join(f"  {k}: {v:+.2f}% (1W)" for k, v in _ranked_s)
_news_lines = "\n".join(f"  [{a['category']}] {a['title']}" for a in news[:10]) if news else "  No news available"
_fred_lines = ""
for lbl, df_f in fred.items():
    if not df_f.empty:
        _fred_lines += f"  {lbl}: {df_f['value'].iloc[-1]:.2f} (as of {df_f['date'].iloc[-1].strftime('%b %Y')})\n"

DASHBOARD_CONTEXT = f"""You are an expert market strategist assistant embedded inside a live weekly market dashboard. Today is {week_end.strftime('%B %d, %Y')}.

=== LIVE INDEX DATA ===
S&P 500:      {_sp.get('current','N/A'):>10} | 1W: {f"{_sp.get('week_chg',0):+.2f}%":>8} | 1M: {f"{_sp.get('month_chg',0):+.2f}%":>8} | YTD: {f"{_sp.get('ytd_chg',0):+.2f}%":>8}
Nasdaq:       {_nq.get('current','N/A'):>10} | 1W: {f"{_nq.get('week_chg',0):+.2f}%":>8} | 1M: {f"{_nq.get('month_chg',0):+.2f}%":>8} | YTD: {f"{_nq.get('ytd_chg',0):+.2f}%":>8}
Dow Jones:    {_dj.get('current','N/A'):>10} | 1W: {f"{_dj.get('week_chg',0):+.2f}%":>8} | 1M: {f"{_dj.get('month_chg',0):+.2f}%":>8} | YTD: {f"{_dj.get('ytd_chg',0):+.2f}%":>8}
Russell 2000: {_ru.get('current','N/A'):>10} | 1W: {f"{_ru.get('week_chg',0):+.2f}%":>8} | 1M: {f"{_ru.get('month_chg',0):+.2f}%":>8} | YTD: {f"{_ru.get('ytd_chg',0):+.2f}%":>8}
VIX:          {_vix.get('current','N/A'):>10} | 1W: {f"{_vix.get('week_chg',0):+.2f}%":>8}
Dev. Markets: {_efa.get('current','N/A'):>10} | 1W: {f"{_efa.get('week_chg',0):+.2f}%":>8}
Emg. Markets: {_eem.get('current','N/A'):>10} | 1W: {f"{_eem.get('week_chg',0):+.2f}%":>8}

=== SECTOR PERFORMANCE (week-over-week, sorted best to worst) ===
{_sec_lines}

=== ECONOMIC INDICATORS (latest FRED data) ===
{_fred_lines if _fred_lines else "  FRED data not loaded (API key required)"}

=== TOP NEWS HEADLINES THIS WEEK ===
{_news_lines}

=== EXECUTIVE SUMMARY (auto-generated from live data) ===
{static_html.replace('<b>','').replace('</b>','').replace('<li>','• ').replace('</li>','')}

You have full knowledge of everything shown on this dashboard. Answer any question about:
- Index or sector performance and why moves happened
- Economic indicators, inflation, interest rates, Fed policy
- Individual companies, sectors, market rotation
- Investment concepts, valuation, macro themes
- News events and their market impact
- Anything else financial markets related

Rules: Be direct and specific. Use the live data above in your answers. 3-6 sentences or bullet points.
No preamble ("Great question!"). No disclaimers unless directly asked. Sound like a CFA charterholder."""

# ── Chat UI ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:20px;background:{CARD};border:1px solid {SLATE};
            border-radius:8px;padding:16px 20px 14px">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <span style="font-size:14px">🤖</span>
        <span style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;
                     color:{GOLD};font-weight:700">Market Assistant</span>
    </div>
    <div style="font-size:11px;color:{SILVER}">
        Ask anything about this week's market data, sectors, economic indicators, individual companies, or macro themes. Web search enabled — ask about current news, prices, or anything outside this dashboard too.
    </div>
</div>""", unsafe_allow_html=True)

# Chat history
if st.session_state["chat_history"]:
    st.markdown("<div style='margin-top:10px'>", unsafe_allow_html=True)
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="background:{NAVY};border-radius:8px;padding:10px 16px;
                        margin:8px 0 4px;border-left:3px solid {GOLD}">
                <div style="font-size:9px;color:{GOLD};font-weight:700;
                            letter-spacing:0.1em;margin-bottom:4px">YOU</div>
                <div style="font-size:13px;color:{WHITE};line-height:1.5">{msg['content']}</div>
            </div>""", unsafe_allow_html=True)
        else:
            # Convert markdown-style bullets to HTML for clean rendering
            import re as _re
            # Strip markdown bold (**text**) and italic (*text*) — render as plain styled text
            raw = msg['content']
            raw = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', raw)   # **bold** → <b>
            raw = _re.sub(r'\*(.+?)\*',   r'<i>\1</i>', raw)       # *italic* → <i>
            # Convert newline bullets to HTML
            raw = raw.replace('\n• ', '<br><span style="margin-right:6px">•</span>')
            raw = raw.replace('\n- ', '<br><span style="margin-right:6px">•</span>')
            raw = raw.replace('\n', '<br>')
            st.markdown(f"""
            <div style="background:{SLATE};border-radius:8px;padding:12px 16px;
                        margin:4px 0 8px;border-left:3px solid {SILVER}">
                <div style="font-size:9px;color:{SILVER};font-weight:700;
                            letter-spacing:0.1em;margin-bottom:6px">MARKET ASSISTANT</div>
                <div style="font-size:13px;color:{TEXT};line-height:1.75;font-family:'Inter','Segoe UI',sans-serif">{raw}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Input area
st.markdown(f'<div style="margin-top:10px">', unsafe_allow_html=True)
user_q = st.text_input(
    "q",
    placeholder="Ask about markets, sectors, rates, companies, or anything on this dashboard…",
    label_visibility="collapsed",
    key="chat_input",
    on_change=lambda: st.session_state.update({"chat_enter_pressed": True}),
)
st.markdown('</div>', unsafe_allow_html=True)

btn_c, clr_c, _ = st.columns([1.2, 1, 6])
with btn_c:
    ask_btn = st.button("Ask →", use_container_width=True, key="chat_ask")
with clr_c:
    if st.session_state["chat_history"]:
        if st.button("Clear", use_container_width=True, key="clear_chat"):
            st.session_state["chat_history"] = []
            st.rerun()

# Trigger on either button click OR Enter key
enter_pressed = st.session_state.pop("chat_enter_pressed", False)
if (ask_btn or enter_pressed) and user_q.strip():
    with st.spinner("Thinking…"):
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1000,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{"role": "user", "content": f"{DASHBOARD_CONTEXT}\n\nUser question: {user_q}"}],
                },
                timeout=30,
            )
            if r.status_code == 200:
                # Extract all text blocks from response (may include tool use)
                blocks = r.json().get("content", [])
                answer = " ".join(
                    b["text"].strip() for b in blocks if b.get("type") == "text" and b.get("text","").strip()
                ) or "No response generated."
            else:
                answer = f"Error {r.status_code}: {r.text[:150]}"
        except Exception as e:
            answer = f"Connection error: {str(e)[:100]}"

    st.session_state["chat_history"].append({"role": "user",      "content": user_q})
    st.session_state["chat_history"].append({"role": "assistant",  "content": answer})
    st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# 2 · MAJOR INDEX PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════

section("02 · Major Index Performance")

if idx_stats:
    rows = []
    for n, s in idx_stats.items():
        rows.append({
            "Index":    n,
            "Current":  f"{s['current']:,.2f}",
            "1W %":     f"{s['week_chg']:+.2f}%"  if s["week_chg"]  is not None else "N/A",
            "1M %":     f"{s['month_chg']:+.2f}%" if s["month_chg"] is not None else "N/A",
            "YTD %":    f"{s['ytd_chg']:+.2f}%"   if s["ytd_chg"]   is not None else "N/A",
            "52W Low":  f"{s['low_52']:,.2f}",
            "52W High": f"{s['high_52']:,.2f}",
            "As of":    str(s.get("date", "")),
        })
    # Build static HTML index table matching sector table style
    pct_cols = ["1W %", "1M %", "YTD %"]

    idx_rows_html = ""
    for r in rows:
        w_clr   = GREEN if r["1W %"].startswith("+")  else (RED if r["1W %"].startswith("-")  else SILVER)
        m_clr   = GREEN if r["1M %"].startswith("+")  else (RED if r["1M %"].startswith("-")  else SILVER)
        ytd_clr = GREEN if r["YTD %"].startswith("+") else (RED if r["YTD %"].startswith("-") else SILVER)
        idx_rows_html += f"""
        <tr style="border-bottom:1px solid {SLATE}">
            <td style="padding:8px 12px;color:{WHITE};font-size:12px;font-weight:600">{r['Index']}</td>
            <td style="padding:8px 12px;color:{WHITE};font-size:12px;text-align:right">{r['Current']}</td>
            <td style="padding:8px 12px;color:{w_clr};font-size:12px;font-weight:600;text-align:right">{r['1W %']}</td>
            <td style="padding:8px 12px;color:{m_clr};font-size:12px;text-align:right">{r['1M %']}</td>
            <td style="padding:8px 12px;color:{ytd_clr};font-size:12px;text-align:right">{r['YTD %']}</td>
            <td style="padding:8px 12px;color:{SILVER};font-size:12px;text-align:right">{r['52W Low']}</td>
            <td style="padding:8px 12px;color:{SILVER};font-size:12px;text-align:right">{r['52W High']}</td>
            <td style="padding:8px 12px;color:{SILVER};font-size:11px;text-align:right">{r['As of']}</td>
        </tr>"""

    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;background:{CARD};
                  border-radius:8px;overflow:hidden;border:1px solid {SLATE};margin-bottom:10px">
        <thead>
            <tr style="background:{NAVY};border-bottom:2px solid {GOLD}">
                <th style="padding:10px 12px;text-align:left;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">Index</th>
                <th style="padding:10px 12px;text-align:right;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">Current</th>
                <th style="padding:10px 12px;text-align:right;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">1W %</th>
                <th style="padding:10px 12px;text-align:right;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">1M %</th>
                <th style="padding:10px 12px;text-align:right;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">YTD %</th>
                <th style="padding:10px 12px;text-align:right;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">52W Low</th>
                <th style="padding:10px 12px;text-align:right;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">52W High</th>
                <th style="padding:10px 12px;text-align:right;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">As of</th>
            </tr>
        </thead>
        <tbody>{idx_rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    df_idx = pd.DataFrame(rows)[["Index","Current","1W %","1M %","YTD %","52W Low","52W High","As of"]]
    st.download_button("⬇ Export Index Table (CSV)", df_idx.to_csv(index=False),
                       file_name=f"indexes_{week_end}.csv", mime="text/csv")

    def index_insight(name, wk, sec_stats, news, vix_chg):
        """Generate a concise one-sentence insight for each index card."""
        if wk is None:
            return ""
        direction = "gained" if wk >= 0 else "fell"
        mag = "sharply" if abs(wk) > 2.5 else ("modestly" if abs(wk) < 0.8 else "")

        # Find top relevant news headline
        top_news = next((a["title"][:60] for a in news[:20]
                         if a["category"] in ("Federal Reserve","Inflation","Earnings",
                                               "Geopolitics","Economic Data")), None)

        # Per-index tailored narrative
        if name == "S&P 500":
            drivers = []
            tech = sec_stats.get("Technology", {}).get("week_chg")
            health = sec_stats.get("Healthcare", {}).get("week_chg")
            if tech and abs(tech) > 2:
                drivers.append(f"tech sector {'drag' if tech < 0 else 'lift'} ({tech:+.1f}%)")
            if health and abs(health) > 2:
                drivers.append(f"healthcare {'strength' if health > 0 else 'weakness'} ({health:+.1f}%)")
            cause = ", ".join(drivers) if drivers else (top_news or "mixed sector performance")
            return f"Broad market {direction} {mag} on {cause}."

        elif name == "Nasdaq":
            tech = sec_stats.get("Technology", {}).get("week_chg")
            comm = sec_stats.get("Comm. Services", {}).get("week_chg")
            if tech and tech < -1.5:
                return f"Growth stocks {direction} {mag} as tech sold off ({tech:+.1f}%), weighing on the index."
            elif tech and tech > 1.5:
                return f"Tech strength ({tech:+.1f}%) drove Nasdaq outperformance vs. the broader market."
            return f"Nasdaq {direction} {mag} amid shifting sentiment on growth and rate expectations."

        elif name == "Dow Jones":
            fin = sec_stats.get("Financials", {}).get("week_chg")
            ind = sec_stats.get("Industrials", {}).get("week_chg")
            if wk > 0 and fin and fin > 0:
                return f"Value and cyclicals held up; financials ({fin:+.1f}%) and industrials provided support."
            elif wk < 0:
                return f"Blue-chip index {direction} {mag} despite defensive sectors offering partial cushion."
            return f"Dow outperformed growth indexes, reflecting rotation into value and cyclical names."

        elif name == "Russell 2000":
            if wk > 1:
                return f"Small-caps rallied {mag}, often signaling improving domestic growth expectations."
            elif wk < -1:
                return f"Small-caps underperformed, reflecting sensitivity to rate concerns and tighter credit conditions."
            return f"Small-cap index {direction} {mag}, tracking broader risk sentiment."

        elif name == "VIX":
            vix_cur = sec_stats.get("VIX", {})
            if wk > 10:
                return f"Fear gauge surged — investors rapidly bought protection amid elevated uncertainty."
            elif wk > 3:
                return f"Volatility rose as markets digested macro headwinds and hedging demand increased."
            elif wk < -5:
                return f"VIX compressed sharply, signaling calmer conditions and reduced demand for downside hedges."
            return f"Volatility {'ticked up' if wk > 0 else 'eased'}, reflecting {'cautious' if wk > 0 else 'improving'} market sentiment."

        elif name == "Dev. Markets":
            if wk > 1:
                return f"Developed market equities gained on USD weakness and improving global growth signals."
            elif wk < -1:
                return f"International developed stocks slipped as dollar strength and global uncertainty weighed."
            return f"EAFE proxy {direction} {mag}, tracking global risk appetite and currency moves."

        elif name == "Emg. Markets":
            if wk > 1:
                return f"EM equities rallied, typically driven by commodity tailwinds or USD softness."
            elif wk < -1:
                return f"Emerging markets fell on dollar strength and risk-off flows out of higher-beta assets."
            return f"EM proxy {direction} {mag}, sensitive to global risk appetite and commodity trends."

        return f"Index {direction} {mag} this week."

    st.markdown("<br>", unsafe_allow_html=True)
    names = list(idx_stats.keys())
    for row_start in range(0, len(names), 4):
        cols = st.columns(4)
        for i, name in enumerate(names[row_start:row_start + 4]):
            s   = idx_stats[name]
            wk  = s.get("week_chg")
            clr = GREEN if (wk or 0) >= 0 else RED
            insight = index_insight(name, wk, sec_stats, news, idx_stats.get("VIX",{}).get("week_chg"))
            with cols[i]:
                # Card with insight + click-to-expand info
                st.markdown(f"""
                <div class="card">
                    <div class="card-label">{name}</div>
                    <div class="card-value">{s['current']:,.2f}</div>
                    <div style="margin-top:5px;display:flex;align-items:baseline;gap:16px;flex-wrap:wrap">
                        <div>
                            {delta_span(wk)}
                            <span style="font-size:9px;color:{SILVER};margin-left:3px;letter-spacing:0.04em">1W</span>
                        </div>
                        <div>
                            <span style="font-size:12px;color:{GREEN if (s.get('month_chg') or 0) >= 0 else RED};font-weight:600">
                                {'▲' if (s.get('month_chg') or 0) >= 0 else '▼'} {abs(s.get('month_chg') or 0):.2f}%
                            </span>
                            <span style="font-size:9px;color:{SILVER};margin-left:3px;letter-spacing:0.04em">1M</span>
                        </div>
                        <div>
                            <span style="font-size:12px;color:{GREEN if (s.get('ytd_chg') or 0) >= 0 else RED};font-weight:600">
                                {'▲' if (s.get('ytd_chg') or 0) >= 0 else '▼'} {abs(s.get('ytd_chg') or 0):.2f}%
                            </span>
                            <span style="font-size:9px;color:{SILVER};margin-left:3px;letter-spacing:0.04em">YTD</span>
                        </div>
                    </div>
                    <div style="font-size:10px;color:{TEXT};margin-top:6px;
                                line-height:1.5;font-style:italic">{insight}</div>
                </div>""", unsafe_allow_html=True)
                if "series" in s and len(s["series"]) > 3:
                    st.markdown(f'<div style="font-size:9px;color:{SILVER};text-align:right;margin-top:-4px;margin-bottom:2px;letter-spacing:0.04em">1 WEEK</div>', unsafe_allow_html=True)
                    st.plotly_chart(sparkline(s["series"], color=clr),
                                    use_container_width=True,
                                    config={"displayModeBar": False})
                info = INDEX_INFO.get(name, {})
                if info:
                    with st.expander(f"ℹ What is the {name}?"):
                        st.markdown(f"""
**{info.get('full_name',name)}**

**What it is:** {info.get('what','')}

**Composition:** {info.get('composition','')}

**Why it matters for markets:** {info.get('why_matters','')}

*Ticker: `{info.get('ticker','')}`*
                        """)
else:
    st.warning("Index data unavailable — check your internet connection and refresh.")

# ═════════════════════════════════════════════════════════════════════════════
# 3 · SECTOR PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════

section("03 · Sector Performance")

if sec_stats:
    sec_rows = [{"Sector": n, "Week %": s.get("week_chg"),
                 "Month %": s.get("month_chg"), "YTD %": s.get("ytd_chg")}
                for n, s in sec_stats.items()]
    df_sec = pd.DataFrame(sec_rows).dropna(subset=["Week %"])

    _dd_level = st.session_state.get("dd_level", "sectors")

    if _dd_level == "sectors":
        col_l, col_r = st.columns([1.1, 1])
        with col_l:
            st.plotly_chart(sector_chart(df_sec), use_container_width=True,
                            config={"displayModeBar": False})
    else:
        # When drilldown is active, use full width for the drill-down view
        col_l = None
        col_r = st.container()

    with col_r:
        best  = df_sec.loc[df_sec["Week %"].idxmax()]
        worst = df_sec.loc[df_sec["Week %"].idxmin()]

        df_disp = df_sec.copy().sort_values("Week %", ascending=False)
        for col in ["Week %", "Month %", "YTD %"]:
            df_disp[col] = df_disp[col].apply(
                lambda v: f"{v:+.2f}%" if pd.notna(v) else "N/A")

        # ── Determine current view level ──────────────────────────────────────
        dd_level  = st.session_state.get("dd_level", "sectors")
        dd_sector = st.session_state.get("dd_sector", "")
        dd_ind    = st.session_state.get("dd_ind", "")

        # ── Breadcrumb nav ────────────────────────────────────────────────────
        if dd_level != "sectors":
            crumb_parts = [f'<span style="color:{GOLD};font-size:11px">All Sectors</span>']
            if dd_level in ("industries", "companies"):
                crumb_parts.append(f'<span style="color:{SILVER};margin:0 5px">›</span>'
                                   f'<span style="color:{GOLD if dd_level=="industries" else TEXT};font-size:11px">{dd_sector}</span>')
            if dd_level == "companies":
                crumb_parts.append(f'<span style="color:{SILVER};margin:0 5px">›</span>'
                                   f'<span style="color:{TEXT};font-size:11px">{dd_ind}</span>')
            st.markdown(
                f'<div style="background:{NAVY};border-radius:6px;padding:8px 14px;'
                f'margin-bottom:10px;border-left:2px solid {GOLD}">'
                + "".join(crumb_parts) + "</div>",
                unsafe_allow_html=True,
            )
            if st.button("← Back to All Sectors", key="back_sectors"):
                st.session_state["dd_level"] = "sectors"
                st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # PAGE: ALL SECTORS (default)
        # ══════════════════════════════════════════════════════════════════════
        if dd_level == "sectors":
            # Header row
            h1, h2, h3, h4, h5 = st.columns([3, 1.5, 1.5, 1.5, 0.6])
            with h1:
                st.markdown(f'<div style="padding:8px 4px;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD};font-weight:700;border-bottom:2px solid {GOLD}">Sector</div>', unsafe_allow_html=True)
            with h2:
                st.markdown(f'<div style="padding:8px 4px;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD};font-weight:700;text-align:right;border-bottom:2px solid {GOLD}">Week % <span style="font-size:8px;color:{SILVER};font-weight:400">(1W)</span></div>', unsafe_allow_html=True)
            with h3:
                st.markdown(f'<div style="padding:8px 4px;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD};font-weight:700;text-align:right;border-bottom:2px solid {GOLD}">Month % <span style="font-size:8px;color:{SILVER};font-weight:400">(1M)</span></div>', unsafe_allow_html=True)
            with h4:
                st.markdown(f'<div style="padding:8px 4px;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD};font-weight:700;text-align:right;border-bottom:2px solid {GOLD}">YTD % <span style="font-size:8px;color:{SILVER};font-weight:400">(Jan 1)</span></div>', unsafe_allow_html=True)
            with h5:
                st.markdown(f'<div style="padding:8px 4px;border-bottom:2px solid transparent"></div>', unsafe_allow_html=True)

            # Data rows — all in st.columns so buttons stay perfectly aligned
            for _, row in df_disp.iterrows():
                wclr = GREEN if row["Week %"].startswith("+") else (RED if row["Week %"].startswith("-") else SILVER)
                mclr = GREEN if row["Month %"].startswith("+") else (RED if row["Month %"].startswith("-") else SILVER)
                yclr = GREEN if row["YTD %"].startswith("+") else (RED if row["YTD %"].startswith("-") else SILVER)

                c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 0.6])
                with c1:
                    st.markdown(f'<div style="padding:9px 4px;color:{WHITE};font-size:13px;font-weight:600;border-bottom:1px solid {SLATE}">{row["Sector"]}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div style="padding:9px 4px;color:{wclr};font-size:13px;font-weight:700;text-align:right;border-bottom:1px solid {SLATE}">{row["Week %"]}</div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div style="padding:9px 4px;color:{mclr};font-size:12px;text-align:right;border-bottom:1px solid {SLATE}">{row["Month %"]}</div>', unsafe_allow_html=True)
                with c4:
                    st.markdown(f'<div style="padding:9px 4px;color:{yclr};font-size:12px;text-align:right;border-bottom:1px solid {SLATE}">{row["YTD %"]}</div>', unsafe_allow_html=True)
                with c5:
                    if row["Sector"] in TAXONOMY:
                        if st.button("›", key=f"go_{row['Sector']}", help=f"Explore {row['Sector']}"):
                            st.session_state["dd_level"]  = "industries"
                            st.session_state["dd_sector"] = row["Sector"]
                            st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # PAGE: INDUSTRIES within a sector
        # ══════════════════════════════════════════════════════════════════════
        elif dd_level == "industries":
            sector_data = TAXONOMY.get(dd_sector, {})
            industries  = sector_data.get("industries", {})

            # Get this sector's weekly return from live data
            sec_wk = sec_stats.get(dd_sector, {}).get("week_chg")
            sec_mo = sec_stats.get(dd_sector, {}).get("month_chg")

            st.markdown(f"""
            <div style="margin-bottom:12px">
                <span style="font-size:16px;font-weight:800;color:{WHITE}">{dd_sector}</span>
                <span style="font-size:11px;color:{SILVER};margin-left:10px">{sector_data.get('description','')}</span>
            </div>""", unsafe_allow_html=True)

            # Weekly return explanation box
            if sec_wk is not None:
                wk_clr     = GREEN if sec_wk >= 0 else RED
                wk_arrow   = "▲" if sec_wk >= 0 else "▼"
                wk_dir     = "gained" if sec_wk >= 0 else "declined"
                wk_mag     = "sharply" if abs(sec_wk) > 3 else ("meaningfully" if abs(sec_wk) > 1.5 else "modestly")

                # Build context-aware reason based on sector + market environment
                vix_cur    = idx_stats.get("VIX", {}).get("current", 18)
                sp_wk      = idx_stats.get("S&P 500", {}).get("week_chg", 0) or 0
                risk_off = sp_wk < -1 or vix_cur > 20

                # AI-generated sector explanation using live data + web search
                sector_prompt = f"""You are a market strategist. Write ONE concise sentence (max 2 sentences) explaining why the {dd_sector} sector {wk_dir} {abs(sec_wk):.2f}% this week.

Live context:
- {dd_sector} weekly return: {sec_wk:+.2f}%
- S&P 500: {sp_wk:+.2f}% this week
- VIX: {vix_cur:.1f} ({'elevated' if vix_cur > 20 else 'moderate' if vix_cur > 15 else 'low'})
- Market tone: {'risk-off' if risk_off else 'risk-on'}
- Top news this week: {' | '.join(a['title'] for a in news[:5]) if news else 'N/A'}

Be specific — cite actual market dynamics, news events, or sector-specific drivers. No generic statements. Sound like a CFA analyst."""

                with st.spinner(f"Generating {dd_sector} analysis…"):
                    reason = ai_generate(
                        sector_prompt,
                        f"sector_reason_{dd_sector}_{week_end}_{sec_wk:.2f}",
                        anthropic_key,
                    )
                if not reason:
                    reason = f"{dd_sector} {wk_dir} {wk_mag} this week amid {'risk-off rotation and defensive positioning' if risk_off else 'improving risk appetite and sector-specific momentum'}."

                mo_str = f" | 1M: {sec_mo:+.2f}%" if sec_mo is not None else ""

                st.markdown(f"""
                <div style="background:{CARD};border-left:3px solid {wk_clr};border-radius:6px;
                            padding:12px 16px;margin-bottom:14px">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
                        <span style="font-size:18px;font-weight:800;color:{wk_clr}">
                            {wk_arrow} {abs(sec_wk):.2f}% this week
                        </span>
                        <span style="font-size:11px;color:{SILVER}">{mo_str}</span>
                    </div>
                    <div style="font-size:12px;color:{TEXT};line-height:1.7">{reason}</div>
                </div>""", unsafe_allow_html=True)

            # Table header
            st.markdown(f"""
            <table style="width:100%;border-collapse:collapse;background:{CARD};
                          border-radius:8px;overflow:hidden;border:1px solid {SLATE}">
                <thead>
                    <tr style="background:{NAVY};border-bottom:2px solid {GOLD}">
                        <th style="padding:10px 14px;text-align:left;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">Industry / Sub-Sector</th>
                        <th style="padding:10px 14px;text-align:left;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">Investment Theme</th>
                        <th style="padding:10px 14px;text-align:center;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{GOLD}">Segments</th>
                        <th style="padding:10px 14px;text-align:center;font-size:10px;color:{GOLD}"></th>
                    </tr>
                </thead>
            </table>""", unsafe_allow_html=True)

            for ind_name, ind_data in industries.items():
                n_subs = len(ind_data.get("sub_industries", {}))
                c1, c2, c3, c4 = st.columns([2.5, 3, 0.7, 0.5])
                with c1:
                    st.markdown(f'<div style="padding:8px 4px;color:{WHITE};font-size:13px;font-weight:600;border-bottom:1px solid {SLATE}">{ind_name}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div style="padding:8px 4px;color:{SILVER};font-size:11px;border-bottom:1px solid {SLATE};line-height:1.4">{ind_data.get("theme","")}</div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div style="padding:8px 4px;color:{GOLD};font-size:11px;text-align:center;border-bottom:1px solid {SLATE}">{n_subs} segments</div>', unsafe_allow_html=True)
                with c4:
                    if st.button("›", key=f"ind_{dd_sector}_{ind_name}"):
                        st.session_state["dd_level"] = "companies"
                        st.session_state["dd_ind"]   = ind_name
                        st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        # PAGE: COMPANIES within an industry
        # ══════════════════════════════════════════════════════════════════════
        elif dd_level == "companies":
            sector_data  = TAXONOMY.get(dd_sector, {})
            industry_data = sector_data.get("industries", {}).get(dd_ind, {})
            sub_industries = industry_data.get("sub_industries", {})

            # Back to industries
            if st.button(f"← Back to {dd_sector} Industries", key="back_inds"):
                st.session_state["dd_level"] = "industries"
                st.rerun()

            st.markdown(f"""
            <div style="margin-bottom:14px">
                <span style="font-size:16px;font-weight:800;color:{WHITE}">{dd_ind}</span>
                <span style="font-size:11px;color:{SILVER};margin-left:10px">{industry_data.get('description','')}</span>
                <div style="margin-top:6px;font-size:11px;color:{GOLD}">🎯 {industry_data.get('theme','')}</div>
            </div>""", unsafe_allow_html=True)

            for sub_name, sub_data in sub_industries.items():
                companies = sub_data.get("companies", {})
                st.markdown(f"""
                <div style="font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                            color:{GOLD};border-bottom:1px solid {SLATE};padding-bottom:5px;margin:16px 0 10px">
                    {sub_name}
                    <span style="font-size:10px;color:{SILVER};font-weight:400;text-transform:none;
                                 letter-spacing:0;margin-left:8px">{sub_data.get('description','')}</span>
                </div>""", unsafe_allow_html=True)

                # Company cards
                cols = st.columns(len(companies)) if len(companies) <= 4 else st.columns(4)
                for i, (ticker, co_name) in enumerate(companies.items()):
                    with cols[i % 4]:
                        try:
                            t    = yf.Ticker(ticker)
                            hist = t.history(period="10d")
                            price = round(float(hist["Close"].iloc[-1]), 2) if not hist.empty else None
                            wk_chg = None
                            if len(hist) >= 6:
                                # Use close 5 trading days ago vs latest for true 1W change
                                wk_chg = round((hist["Close"].iloc[-1] - hist["Close"].iloc[-6]) / hist["Close"].iloc[-6] * 100, 2)
                            elif len(hist) >= 2:
                                wk_chg = round((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0] * 100, 2)
                        except Exception:
                            price, wk_chg = None, None

                        clr = GREEN if (wk_chg or 0) >= 0 else RED
                        price_str = f"${price:,.2f}" if price else "N/A"
                        chg_str   = f"{'▲' if (wk_chg or 0)>=0 else '▼'} {abs(wk_chg or 0):.2f}%" if wk_chg is not None else "N/A"

                        st.markdown(f"""
                        <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;
                                    padding:12px 14px;margin-bottom:8px">
                            <div style="font-size:10px;color:{SILVER};letter-spacing:0.08em">{ticker}</div>
                            <div style="font-size:13px;font-weight:700;color:{WHITE};margin-top:2px;
                                        line-height:1.3">{co_name}</div>
                            <div style="font-size:18px;font-weight:800;color:{WHITE};margin-top:6px">{price_str}</div>
                            <div style="color:{clr};font-size:12px;font-weight:600;margin-top:2px">{chg_str}</div>
                        </div>""", unsafe_allow_html=True)

    st.download_button("⬇ Export Sector Table (CSV)", df_sec.to_csv(index=False),
                       file_name=f"sectors_{week_end}.csv", mime="text/csv")

    # Summary box — sits below chart+table as a full-width strip
    best  = df_sec.loc[df_sec["Week %"].idxmax()]
    worst = df_sec.loc[df_sec["Week %"].idxmin()]
    st.markdown(f"""
    <div class="sbox" style="margin-top:12px;display:flex;gap:32px;align-items:center;flex-wrap:wrap">
        <div>🟢 <b>Top Sector:</b> {best['Sector']}
            <span class="up"> ▲ {best['Week %']:+.2f}%</span>
        </div>
        <div>🔴 <b>Lagging Sector:</b> {worst['Sector']}
            <span class="dn"> ▼ {worst['Week %']:.2f}%</span>
        </div>
        <div style="font-size:11px;color:{SILVER};flex:1;min-width:200px">
            Defensive leadership (Utilities, Staples, Healthcare) signals risk-off sentiment.
            Cyclical leadership (Tech, Financials, Consumer Disc.) signals risk-on positioning.
        </div>
    </div>""", unsafe_allow_html=True)
else:
    st.warning("Sector data unavailable.")

# ═════════════════════════════════════════════════════════════════════════════
# 4 · INFLATION & ECONOMIC DATA
# ═════════════════════════════════════════════════════════════════════════════

section("04 · Inflation & Economic Data")

ECON_LABELS = [k for k in FRED_SERIES
               if k not in ("Fed Funds Rate", "10Y Treasury", "2Y Treasury")]

if not fred_key:
    st.info(
        "🔑 **Enter your FRED API key in the sidebar** to unlock economic indicators. "
        "Free key at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html).",
        icon="ℹ️",
    )
else:
    for i in range(0, len(ECON_LABELS), 4):
        batch = ECON_LABELS[i:i + 4]
        cols  = st.columns(len(batch))
        for j, label in enumerate(batch):
            df_f = fred.get(label, pd.DataFrame())
            _, _, unit = FRED_SERIES[label]
            with cols[j]:
                if df_f.empty:
                    st.warning(f"{label}: no data")
                    continue
                cur  = df_f["value"].iloc[-1]
                prev = df_f["value"].iloc[-2] if len(df_f) >= 2 else None
                # Show % change for level series (retail sales, GDP etc), absolute for rate/% series
                rate_series = {"CPI", "Core CPI", "PCE", "Core PCE", "Unemployment",
                               "Fed Funds Rate", "10Y Treasury", "2Y Treasury"}
                if label in rate_series:
                    chg = round(cur - prev, 3) if prev is not None else None
                    chg_str = f"{chg:+.3f} {unit}" if chg is not None else None
                else:
                    # % change from previous reading
                    chg_pct = round((cur - prev) / prev * 100, 2) if prev and prev != 0 else None
                    chg = chg_pct
                    chg_str = f"{chg_pct:+.2f}%" if chg_pct is not None else None
                d = df_f["date"].iloc[-1].strftime("%b %Y")
                card(label, f"{cur:,.2f} {unit}", delta_span(chg),
                     f"prev: {prev:.2f} · {d}")
                st.plotly_chart(fred_chart(df_f), use_container_width=True,
                                config={"displayModeBar": False})
                finfo = FRED_INFO.get(label, {})
                if finfo:
                    with st.expander(f"ℹ What is {label}?"):
                        st.markdown(f"""
**{finfo.get('full_name', label)}**

**What it measures:** {finfo.get('what','')}

**Why it matters for markets:** {finfo.get('why_matters','')}

*Source: {finfo.get('source','')}*
                        """)

# ═════════════════════════════════════════════════════════════════════════════
# 5 · INTEREST RATES & FED WATCH
# ═════════════════════════════════════════════════════════════════════════════

section("05 · Interest Rates & Fed Watch")

col_l, col_r = st.columns([3, 2])

with col_l:
    df_2y  = fred.get("2Y Treasury",    pd.DataFrame())
    df_10y = fred.get("10Y Treasury",   pd.DataFrame())
    df_ff  = fred.get("Fed Funds Rate", pd.DataFrame())

    if not fred_key:
        st.info("Enter your FRED API key in the sidebar to view rate charts.")
    else:
        r_cols = st.columns(3)
        for ci, (lbl, dfr) in enumerate(
            [("Fed Funds", df_ff), ("2Y Yield", df_2y), ("10Y Yield", df_10y)]
        ):
            with r_cols[ci]:
                if dfr.empty:
                    st.warning(f"{lbl}: no data")
                else:
                    cur  = dfr["value"].iloc[-1]
                    prev = dfr["value"].iloc[-2] if len(dfr) >= 2 else None
                    chg  = round(cur - prev, 3) if prev is not None else None
                    card(lbl, f"{cur:.2f}%", delta_span(chg, invert=True))
                    rinfo = FRED_INFO.get(lbl, {})
                    if rinfo:
                        with st.expander(f"ℹ What is {lbl}?"):
                            st.markdown(f"""
**{rinfo.get('full_name', lbl)}**

**What it is:** {rinfo.get('what','')}

**Why it matters:** {rinfo.get('why_matters','')}

*Source: {rinfo.get('source','')}*
                            """)

        if not df_2y.empty and not df_10y.empty:
            m = pd.merge(df_2y.rename(columns={"value": "y2"}),
                         df_10y.rename(columns={"value": "y10"}),
                         on="date", how="inner")
            spread = round(m["y10"].iloc[-1] - m["y2"].iloc[-1], 2)
            clr    = GREEN if spread >= 0 else RED
            st.markdown(f"""
            <div class="card" style="border-color:{clr}">
                <div class="card-label">2s / 10s Yield Curve Spread</div>
                <div class="card-value" style="color:{clr}">{spread:+.2f}%</div>
                <div style="font-size:11px;color:{TEXT};margin-top:3px">
                    {"Normal (positive slope)" if spread >= 0
                     else "Inverted — historically a recession signal"}
                </div>
            </div>""", unsafe_allow_html=True)

        st.plotly_chart(yield_chart(df_2y, df_10y), use_container_width=True,
                        config={"displayModeBar": False})

with col_r:

    @st.cache_data(ttl=10800, show_spinner=False)  # refresh every 3 hours
    def fetch_fed_analysis(today_str: str, api_key: str) -> dict:
        """Use AI + web search to get current Fed stance, rate expectations, next meeting."""
        if not api_key:
            return {}
        prompt = f"""Today is {today_str}. Search the web and return a JSON object with the current Federal Reserve monetary policy situation.

Return ONLY this exact JSON structure with no other text:
{{
  "current_rate": "X.XX%",
  "stance": "2-3 sentence summary of current FOMC stance and policy direction based on most recent Fed communications",
  "next_meeting": "Date of next FOMC meeting",
  "rate_decision_odds": "What the market currently expects at the next meeting (e.g. 85% hold, 15% cut)",
  "recent_commentary": "1-2 sentences on most recent Fed speaker comments or FOMC minutes key takeaway",
  "inflation_status": "Brief current inflation vs 2% target status",
  "last_updated": "{today_str}"
}}

Search for: current fed funds rate 2026, FOMC next meeting date, CME fedwatch probabilities, latest Federal Reserve statement, recent Fed chair Powell comments."""

        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": "claude-sonnet-4-6", "max_tokens": 800,
                      "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=30,
            )
            if r.status_code == 200:
                import json as _json
                blocks = r.json().get("content", [])
                text = " ".join(b["text"].strip() for b in blocks if b.get("type") == "text")
                start = text.find("{")
                end   = text.rfind("}") + 1
                if start >= 0 and end > start:
                    return _json.loads(text[start:end])
        except Exception:
            pass
        return {}

    fed = fetch_fed_analysis(date.today().strftime("%B %d, %Y"), anthropic_key)

    def clean(s):
        import re as _re
        return _re.sub(r'<[^>]+>', '', str(s)).strip() if s else ""

    # Build fed content as individual lines to avoid f-string HTML rendering issues
    g = GOLD; w = WHITE; s = SILVER; t = TEXT; sl = SLATE

    if fed:
        rate    = clean(fed.get("current_rate", "N/A"))
        stance  = clean(fed.get("stance", ""))
        meeting = clean(fed.get("next_meeting", ""))
        odds    = clean(fed.get("rate_decision_odds", ""))
        comment = clean(fed.get("recent_commentary", ""))
        infl    = clean(fed.get("inflation_status", ""))
        updated = clean(fed.get("last_updated", ""))

        fed_html = (
            f'<div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;padding:16px 18px">'
            f'<div style="font-size:10px;letter-spacing:0.09em;text-transform:uppercase;color:{SILVER};margin-bottom:12px">Federal Reserve — Live Analysis</div>'
            f'<div style="margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:{GOLD}">Current Rate</span><br>'
            f'<span style="font-size:20px;font-weight:800;color:{WHITE}">{rate}</span>'
            f'<span style="font-size:10px;color:{SILVER};margin-left:8px">Federal Funds Rate</span></div>'
            f'<div style="margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:{GOLD}">FOMC Stance</span><br>'
            f'<span style="font-size:12px;color:{TEXT};line-height:1.7">{stance}</span></div>'
            f'<div style="margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:{GOLD}">Next Meeting</span><br>'
            f'<span style="font-size:12px;color:{TEXT}">{meeting}</span><br>'
            f'<span style="font-size:11px;color:{SILVER}">Market odds: {odds}</span></div>'
            f'<div style="margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:{GOLD}">Latest Commentary</span><br>'
            f'<span style="font-size:12px;color:{TEXT};line-height:1.7">{comment}</span></div>'
            f'<div style="margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:{GOLD}">Inflation vs Target</span><br>'
            f'<span style="font-size:12px;color:{TEXT}">{infl}</span></div>'
            f'<div style="font-size:10px;color:{SILVER};border-top:1px solid {SLATE};padding-top:8px;margin-top:4px">'
            f'AI-updated · {updated} · Refreshes every 3 hours</div>'
            f'<div style="font-size:11px;border-top:1px solid {SLATE};padding-top:10px;margin-top:6px;color:{TEXT}">'
            f'<b>Official Sources</b><br>'
            f'· <a href="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm" style="color:{GOLD}" target="_blank">FOMC Calendar</a><br>'
            f'· <a href="https://www.federalreserve.gov/monetarypolicy/beigebook/" style="color:{GOLD}" target="_blank">Fed Beige Book</a><br>'
            f'· <a href="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html" style="color:{GOLD}" target="_blank">CME FedWatch Tool</a><br>'
            f'· <a href="https://fred.stlouisfed.org" style="color:{GOLD}" target="_blank">FRED Economic Data</a>'
            f'</div></div>'
        )
        st.markdown(fed_html, unsafe_allow_html=True)

    else:
        fed_html = (
            f'<div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;padding:16px 18px">'
            f'<div style="font-size:10px;letter-spacing:0.09em;text-transform:uppercase;color:{SILVER};margin-bottom:12px">Federal Reserve — Key Context</div>'
            f'<div style="margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:{GOLD}">Current Stance</span><br>'
            f'<span style="font-size:12px;color:{TEXT}">The FOMC maintains a data-dependent approach. CPI and PCE prints are closely watched to anticipate the timing of future rate adjustments.</span></div>'
            f'<div style="margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:{GOLD}">Market Expectations</span><br>'
            f'<span style="font-size:12px;color:{TEXT}">See the CME FedWatch Tool for live implied probabilities of rate moves at each upcoming meeting.</span></div>'
            f'<div style="font-size:11px;border-top:1px solid {SLATE};padding-top:10px;margin-top:6px;color:{TEXT}">'
            f'<b>Official Sources</b><br>'
            f'· <a href="https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm" style="color:{GOLD}" target="_blank">FOMC Calendar</a><br>'
            f'· <a href="https://www.federalreserve.gov/monetarypolicy/beigebook/" style="color:{GOLD}" target="_blank">Fed Beige Book</a><br>'
            f'· <a href="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html" style="color:{GOLD}" target="_blank">CME FedWatch Tool</a><br>'
            f'· <a href="https://fred.stlouisfed.org" style="color:{GOLD}" target="_blank">FRED Economic Data</a>'
            f'</div></div>'
        )
        st.markdown(fed_html, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 6 · MARKET-MOVING NEWS
# ═════════════════════════════════════════════════════════════════════════════

section("06 · Market-Moving News")

CAT_ORDER = ["Federal Reserve", "Inflation", "Economic Data",
             "Earnings", "Geopolitics", "Sector News", "Market News"]

if not news:
    st.warning("No news loaded — check your internet connection.")
else:
    avail_cats = sorted({a["category"] for a in news})
    sel = st.multiselect("Filter by category", avail_cats, default=avail_cats,
                         label_visibility="collapsed")
    filtered = [a for a in news if a["category"] in sel]
    grouped: dict[str, list] = {}
    for a in filtered:
        grouped.setdefault(a["category"], []).append(a)

    for cat in CAT_ORDER:
        arts = grouped.get(cat, [])
        if not arts:
            continue
        st.markdown(
            f'<div style="font-size:10px;font-weight:700;letter-spacing:0.09em;'
            f'text-transform:uppercase;color:{SILVER};margin:14px 0 5px">'
            f'{cat} &nbsp;·&nbsp; {len(arts)} article{"s" if len(arts)!=1 else ""}</div>',
            unsafe_allow_html=True)
        cols = st.columns(2)
        for i, a in enumerate(arts[:8]):
            with cols[i % 2]:
                _title   = a["title"][:120] + ("…" if len(a["title"]) > 120 else "")
                _summary = a["summary"][:220] + ("…" if len(a["summary"]) > 220 else "")
                st.markdown(f"""
                <div class="ncard">
                    <div class="ntitle">
                        <a href="{a['link']}" target="_blank">{_title}</a>
                    </div>
                    <div class="nmeta">{a['source']} · {a['pub']}</div>
                    <div class="nbody">{_summary}</div>
                </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 7 · UPCOMING EVENTS CALENDAR
# ═════════════════════════════════════════════════════════════════════════════

section("07 · Upcoming Events Calendar")

@st.cache_data(ttl=21600, show_spinner=False)  # refresh every 6 hours
def fetch_ai_events(today_str: str, api_key: str) -> list:
    """Use AI + web search to find upcoming market-moving events, auto-filtered to future dates."""
    if not api_key:
        return []
    prompt = f"""Today is {today_str}. Search the web and return a JSON list of upcoming market-moving economic events, data releases, Fed meetings, and major earnings for the next 4 weeks.

For each event return exactly this JSON structure:
{{"date": "Mon DD, YYYY", "event": "Event name", "cat": "Category", "detail": "One sentence on why this matters for markets"}}

Categories must be one of: Fed, Inflation, Jobs, GDP, Economic Data, Earnings

Rules:
- Only include events that have NOT happened yet (after {today_str})
- Include: FOMC meetings, CPI, PCE, PPI, jobs report, GDP releases, retail sales, major earnings (NVDA, AAPL, MSFT, GOOGL, META, AMZN, JPM etc), ISM PMI, consumer sentiment, housing data, Treasury auctions
- Sort by date ascending
- Return 16-24 events
- Return ONLY valid JSON array, no other text, no markdown code blocks

Example format:
[{{"date": "Jul 10, 2026", "event": "CPI Release (June)", "cat": "Inflation", "detail": "Key Fed input — a hot print could delay rate cuts and pressure equity valuations."}}]"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 2000,
                  "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=45,
        )
        if r.status_code == 200:
            blocks = r.json().get("content", [])
            text = " ".join(b["text"].strip() for b in blocks if b.get("type") == "text")
            # Extract JSON array from response
            import json as _json
            start = text.find("[")
            end   = text.rfind("]") + 1
            if start >= 0 and end > start:
                raw = _json.loads(text[start:end])
                # Filter out any past events
                today_dt = date.today()
                filtered = []
                for ev in raw:
                    try:
                        ev_date = pd.to_datetime(ev["date"]).date()
                        if ev_date >= today_dt:
                            filtered.append(ev)
                    except Exception:
                        filtered.append(ev)  # include if date can't be parsed
                return filtered
    except Exception:
        pass
    return []


# Show calendar with AI auto-fetch
today_str = date.today().strftime("%B %d, %Y")
ai_events = fetch_ai_events(today_str, anthropic_key)

if ai_events:
    st.markdown(
        f'<div style="font-size:10px;color:{SILVER};margin-bottom:10px">'
        f'Auto-updated via AI web search · Past events removed automatically · '
        f'Refreshes every 6 hours · {len(ai_events)} upcoming events found</div>',
        unsafe_allow_html=True)

    CAT_COLORS = {
        "Fed": BLUE, "Inflation": RED, "Jobs": GREEN,
        "GDP": GOLD, "Economic Data": SILVER, "Earnings": "#A07FE0",
    }

    # Category filter
    all_cats  = list(dict.fromkeys(e.get("cat","Other") for e in ai_events))
    sel_cats  = st.multiselect("Filter events", all_cats, default=all_cats,
                                key="cal", label_visibility="collapsed")
    fil_ev    = [e for e in ai_events if e.get("cat","Other") in sel_cats]

    cols = st.columns(2)
    for i, ev in enumerate(fil_ev):
        clr = CAT_COLORS.get(ev.get("cat","Other"), SILVER)
        detail = ev.get("detail", "")
        with cols[i % 2]:
            st.markdown(f"""
            <div class="cevent" style="border-left-color:{clr};padding:10px 14px;margin-bottom:6px">
                <div class="cdate">{ev.get('date','')} · {ev.get('cat','')}</div>
                <div style="margin-top:3px;color:{WHITE};font-size:12px;font-weight:600">{ev.get('event','')}</div>
                {f'<div style="margin-top:3px;color:{SILVER};font-size:10px;line-height:1.5">{detail}</div>' if detail else ''}
            </div>""", unsafe_allow_html=True)

else:
    # Fallback to manual events if AI unavailable
    st.markdown(
        f'<div style="font-size:10px;color:{SILVER};margin-bottom:10px">'
        f'AI calendar unavailable — showing manually entered events.</div>',
        unsafe_allow_html=True)
    events   = upcoming_events()
    today_dt = date.today()
    valid = []
    for e in events:
        try:
            if pd.to_datetime(e["date"]).date() >= today_dt:
                valid.append(e)
        except Exception:
            valid.append(e)
    events = valid
    all_cats = list(dict.fromkeys(e["cat"] for e in events))
    sel_cats = st.multiselect("Filter events", all_cats, default=all_cats,
                               key="cal", label_visibility="collapsed")
    fil_ev   = [e for e in events if e["cat"] in sel_cats]
    cols = st.columns(2)
    for i, ev in enumerate(fil_ev):
        clr = cat_color(ev["cat"])
        with cols[i % 2]:
            st.markdown(f"""
            <div class="cevent" style="border-left-color:{clr}">
                <div class="cdate">{ev['date']} · {ev['cat']}</div>
                <div style="margin-top:2px;color:{TEXT}">{ev['event']}</div>
            </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════════════

# ── Appendix ─────────────────────────────────────────────────────────────────
section("Appendix · Data Sources & Methodology")

SOURCES = [
    ("Index Performance",        "End-of-day prices (OHLCV)",                      "Yahoo Finance (yfinance)",                   "Daily · 15–20 min delay"),
    ("Sector Performance",       "SPDR Sector ETF prices (XLK, XLF, XLV…)",        "Yahoo Finance (yfinance)",                   "Daily · 15–20 min delay"),
    ("CPI / Core CPI",           "CPIAUCSL, CPILFESL series",                       "FRED® · Bureau of Labor Statistics",         "Monthly release"),
    ("PCE / Core PCE",           "PCEPI, PCEPILFE series",                          "FRED® · Bureau of Economic Analysis",        "Monthly release"),
    ("Unemployment Rate",        "UNRATE series (U-3)",                             "FRED® · Bureau of Labor Statistics",         "Monthly (Jobs Report)"),
    ("Real GDP",                 "GDPC1 series (Chained 2017 $)",                   "FRED® · Bureau of Economic Analysis",        "Quarterly"),
    ("Retail Sales",             "RSAFS series (Advance Retail Trade)",             "FRED® · U.S. Census Bureau",                 "Monthly release"),
    ("Consumer Sentiment",       "UMCSENT series",                                  "FRED® · University of Michigan",             "Monthly (prelim + final)"),
    ("Fed Funds Rate",           "FEDFUNDS series (effective rate)",                "FRED® · Federal Reserve",                    "Monthly (FOMC meetings)"),
    ("Treasury Yields (2Y/10Y)", "DGS2, DGS10 series",                             "FRED® · U.S. Treasury",                     "Daily"),
    ("Market News",              "RSS feeds (headlines + summaries)",               "Reuters, Yahoo Finance, AP, CNBC, MarketWatch","Real-time · 30 min cache"),
    ("Company Drill-Down",       "Price, market cap, P/E, margins",                "Yahoo Finance (yfinance)",                   "Daily · 15 min cache"),
    ("Upcoming Events",          "Manually curated weekly",                         "BLS, BEA, Federal Reserve, U.S. Census",     "Updated weekly"),
]

# Table header
header_html = f"""
<table style="width:100%;border-collapse:collapse;font-size:11px;margin-bottom:20px;background:{CARD};border-radius:8px;overflow:hidden;border:1px solid {SLATE}">
<thead>
  <tr style="background:{NAVY};border-bottom:2px solid {GOLD}">
    <th style="padding:8px 12px;text-align:left;color:{GOLD};font-size:10px;letter-spacing:0.08em;text-transform:uppercase">Dashboard Section</th>
    <th style="padding:8px 12px;text-align:left;color:{GOLD};font-size:10px;letter-spacing:0.08em;text-transform:uppercase">Data Series</th>
    <th style="padding:8px 12px;text-align:left;color:{GOLD};font-size:10px;letter-spacing:0.08em;text-transform:uppercase">Provider</th>
    <th style="padding:8px 12px;text-align:left;color:{GOLD};font-size:10px;letter-spacing:0.08em;text-transform:uppercase">Frequency</th>
  </tr>
</thead><tbody>"""

rows_html = ""
for i, (section_name, series, provider, freq) in enumerate(SOURCES):
    bg = CARD if i % 2 == 0 else NAVY
    rows_html += f"""<tr style="background:{bg};border-bottom:1px solid {SLATE}">
    <td style="padding:8px 12px;color:{WHITE};font-size:11px;font-weight:600">{section_name}</td>
    <td style="padding:8px 12px;color:{TEXT};font-size:11px">{series}</td>
    <td style="padding:8px 12px;color:{TEXT};font-size:11px">{provider}</td>
    <td style="padding:8px 12px;color:{SILVER};font-size:11px">{freq}</td>
  </tr>"""

st.markdown(header_html + rows_html + "</tbody></table>", unsafe_allow_html=True)

# Methodology
m1, m2 = st.columns(2)
with m1:
    st.markdown(f"""
    <div style="background:{CARD};border-radius:6px;padding:12px 16px;border:1px solid {SLATE}">
        <div style="color:{WHITE};font-size:12px;font-weight:700;margin-bottom:8px">Performance Return Calculations</div>
        <div style="color:{TEXT};font-size:11px;line-height:1.8">
            · <b>1W %</b>: Current close vs. close 5 trading days prior<br>
            · <b>1M %</b>: Current close vs. close ~21 trading days prior<br>
            · <b>YTD %</b>: Current close vs. first trading day of the year<br>
            · <b>52W High/Low</b>: Rolling 252-day intraday high and low<br>
            · All returns are price returns (dividends excluded)
        </div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div style="background:{CARD};border-radius:6px;padding:12px 16px;border:1px solid {SLATE}">
        <div style="color:{WHITE};font-size:12px;font-weight:700;margin-bottom:8px">Economic Indicator Changes</div>
        <div style="color:{TEXT};font-size:11px;line-height:1.8">
            · <b>Rate series</b> (CPI, PCE, Unemployment, Fed Funds, Yields): absolute point change from prior reading<br>
            · <b>Level series</b> (GDP, Retail Sales, Sentiment): % change from prior reading<br>
            · FRED data reflects latest official release and is subject to revision
        </div>
    </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div style="margin-top:16px;font-size:10px;color:{SILVER};line-height:1.9;
            border-top:1px solid {SLATE};padding-top:14px;text-align:center">
    For <b>informational purposes only</b>. Not investment advice. Data from publicly available
    free APIs — may be delayed, revised, or subject to error. Verify through primary sources
    before making investment decisions. &nbsp;·&nbsp; Built by Emmitt Macor · {datetime.now().strftime('%Y')}
</div>""", unsafe_allow_html=True)
