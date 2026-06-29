"""
drilldown.py  —  Bloomberg-style sector drill-down module
Integrates with app.py via st.session_state navigation.
"""

import re
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ── Color palette (must match app.py) ────────────────────────────────────────
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
TEXT   = "#D8E4F0"

# ═════════════════════════════════════════════════════════════════════════════
# TAXONOMY  — Sector → Industry → Sub-Industry → Companies
# ═════════════════════════════════════════════════════════════════════════════

TAXONOMY = {
    "Technology": {
        "etf": "XLK",
        "description": "Companies involved in the design, development, and support of computer hardware, software, internet infrastructure, and IT services.",
        "industries": {
            "Semiconductors": {
                "description": "Design and manufacture of integrated circuits, processors, memory chips, and related equipment.",
                "theme": "AI infrastructure buildout driving unprecedented demand for GPUs, HBM memory, and advanced packaging.",
                "market_size": "$600B+",
                "sub_industries": {
                    "GPU & AI Accelerators": {
                        "companies": {"NVDA": "NVIDIA", "AMD": "AMD", "INTC": "Intel"},
                        "description": "Graphics and AI compute chips powering data centers and generative AI workloads."
                    },
                    "Foundries": {
                        "companies": {"TSM": "TSMC", "INTC": "Intel Foundry", "GFS": "GlobalFoundries"},
                        "description": "Contract chip manufacturers that fabricate designs for fabless companies."
                    },
                    "Memory": {
                        "companies": {"MU": "Micron", "005930.KS": "Samsung (KRX)", "000660.KS": "SK Hynix (KRX)"},
                        "description": "DRAM, NAND flash, and HBM memory chips for computing and storage."
                    },
                    "Analog & Power": {
                        "companies": {"TXN": "Texas Instruments", "ADI": "Analog Devices", "MCHP": "Microchip"},
                        "description": "Chips that process real-world signals and manage power delivery."
                    },
                    "Semiconductor Equipment": {
                        "companies": {"AMAT": "Applied Materials", "LRCX": "Lam Research", "ASML": "ASML"},
                        "description": "Tools and machines used to manufacture semiconductor chips."
                    },
                    "FPGA & ASIC": {
                        "companies": {"AMD": "AMD (Xilinx)", "INTC": "Intel (Altera)", "MRVL": "Marvell"},
                        "description": "Programmable and custom-designed logic chips for specific workloads."
                    },
                },
            },
            "Software": {
                "description": "Enterprise, cloud, and consumer software platforms.",
                "theme": "AI integration driving re-acceleration of software spend and seat expansion.",
                "market_size": "$700B+",
                "sub_industries": {
                    "Cloud Platforms": {"companies": {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon"}, "description": "Hyperscale cloud infrastructure and platform services."},
                    "Enterprise Software": {"companies": {"CRM": "Salesforce", "NOW": "ServiceNow", "ORCL": "Oracle"}, "description": "Business applications for CRM, ERP, ITSM, and workflow automation."},
                    "Cybersecurity": {"companies": {"CRWD": "CrowdStrike", "PANW": "Palo Alto", "ZS": "Zscaler"}, "description": "Endpoint, network, and cloud security platforms."},
                    "AI Software": {"companies": {"MSFT": "Microsoft", "GOOGL": "Alphabet", "SNOW": "Snowflake"}, "description": "AI-native and AI-enhanced software applications."},
                },
            },
            "Hardware & Networking": {
                "description": "Physical computing devices, networking equipment, and infrastructure.",
                "theme": "AI cluster buildout driving strong demand for networking and server hardware.",
                "market_size": "$400B+",
                "sub_industries": {
                    "Networking": {"companies": {"CSCO": "Cisco", "ANET": "Arista", "MRVL": "Marvell"}, "description": "Switches, routers, and networking silicon for data centers."},
                    "Servers & Storage": {"companies": {"DELL": "Dell", "HPE": "HP Enterprise", "STX": "Seagate"}, "description": "Server hardware and enterprise storage systems."},
                    "Consumer Electronics": {"companies": {"AAPL": "Apple", "MSFT": "Microsoft Surface", "HPQ": "HP"}, "description": "PCs, tablets, wearables, and consumer devices."},
                },
            },
        },
    },
    "Healthcare": {
        "etf": "XLV",
        "description": "Companies providing healthcare equipment, services, pharmaceuticals, biotechnology, and insurance.",
        "industries": {
            "Pharmaceuticals": {
                "description": "Development and commercialization of branded and generic drugs.",
                "theme": "GLP-1 obesity drugs and oncology pipelines driving sector rotation and M&A.",
                "market_size": "$1.5T+",
                "sub_industries": {
                    "Large Cap Pharma": {"companies": {"LLY": "Eli Lilly", "JNJ": "J&J", "MRK": "Merck"}, "description": "Major diversified pharmaceutical companies with broad drug portfolios."},
                    "Specialty Pharma": {"companies": {"ABBV": "AbbVie", "BMY": "Bristol Myers", "GILD": "Gilead"}, "description": "Focused on specific therapeutic areas like oncology, immunology, virology."},
                    "Obesity/GLP-1": {"companies": {"LLY": "Eli Lilly", "NVO": "Novo Nordisk"}, "description": "GLP-1 receptor agonists for obesity and diabetes — the fastest-growing drug class."},
                },
            },
            "Biotechnology": {
                "description": "Drug discovery using biological systems — highest risk/reward in healthcare.",
                "theme": "AI-driven drug discovery and cell/gene therapy commercialization.",
                "market_size": "$800B+",
                "sub_industries": {
                    "Large Cap Biotech": {"companies": {"AMGN": "Amgen", "REGN": "Regeneron", "VRTX": "Vertex"}, "description": "Established biotech with commercial-stage products and strong pipelines."},
                    "Cell & Gene Therapy": {"companies": {"BLUE": "bluebird bio", "CRSP": "CRISPR Therapeutics", "NTLA": "Intellia"}, "description": "Next-generation therapies that edit or replace faulty genes."},
                },
            },
            "Medical Devices": {
                "description": "Equipment, instruments, and implants used in medical procedures.",
                "theme": "Robotic surgery and minimally invasive procedure adoption driving volume growth.",
                "market_size": "$500B+",
                "sub_industries": {
                    "Surgical Robots": {"companies": {"ISRG": "Intuitive Surgical", "MZOR": "Mazor Robotics"}, "description": "Robotic-assisted surgical systems reducing recovery time and complications."},
                    "Cardiovascular Devices": {"companies": {"ABT": "Abbott", "BSX": "Boston Scientific", "MDT": "Medtronic"}, "description": "Stents, pacemakers, and cardiac monitoring devices."},
                },
            },
        },
    },
    "Financials": {
        "etf": "XLF",
        "description": "Banks, insurance companies, asset managers, exchanges, and fintech platforms.",
        "industries": {
            "Banks": {
                "description": "Commercial and investment banking, lending, and deposit services.",
                "theme": "Net interest margin compression vs. trading revenue strength; M&A advisory rebound.",
                "market_size": "$2T+ market cap",
                "sub_industries": {
                    "Money Center Banks": {"companies": {"JPM": "JPMorgan", "BAC": "Bank of America", "C": "Citigroup"}, "description": "Largest U.S. banks with global operations across all banking segments."},
                    "Investment Banks": {"companies": {"GS": "Goldman Sachs", "MS": "Morgan Stanley"}, "description": "Capital markets, M&A advisory, and asset management."},
                    "Regional Banks": {"companies": {"USB": "US Bancorp", "PNC": "PNC Financial", "RF": "Regions"}, "description": "Mid-size banks focused on specific U.S. geographic markets."},
                },
            },
            "Asset Management": {
                "description": "Investment management, wealth management, and alternative assets.",
                "theme": "Private credit and alternatives AUM growth driving fee expansion.",
                "market_size": "$100T+ AUM globally",
                "sub_industries": {
                    "Traditional Asset Managers": {"companies": {"BLK": "BlackRock", "TROW": "T. Rowe Price", "IVZ": "Invesco"}, "description": "Mutual fund and ETF managers with broad public market strategies."},
                    "Alternative Asset Managers": {"companies": {"BX": "Blackstone", "KKR": "KKR", "APO": "Apollo"}, "description": "Private equity, private credit, real estate, and infrastructure managers."},
                },
            },
            "Insurance": {
                "description": "Property & casualty, life, health, and specialty insurance underwriters.",
                "theme": "Hard market pricing environment supporting premium growth and underwriting margins.",
                "market_size": "$1T+ premiums",
                "sub_industries": {
                    "P&C Insurance": {"companies": {"PGR": "Progressive", "ALL": "Allstate", "CB": "Chubb"}, "description": "Property and casualty insurance for auto, home, and commercial risks."},
                    "Life & Health": {"companies": {"MET": "MetLife", "PRU": "Prudential", "UNH": "UnitedHealth"}, "description": "Life insurance, annuities, and managed care."},
                },
            },
        },
    },
    "Energy": {
        "etf": "XLE",
        "description": "Companies engaged in the exploration, production, refining, and distribution of oil, gas, and renewable energy.",
        "industries": {
            "Integrated Oil & Gas": {
                "description": "Vertically integrated energy majors operating across the full value chain.",
                "theme": "Capital discipline and shareholder returns; transition energy investments.",
                "market_size": "$2T+ market cap",
                "sub_industries": {
                    "Oil Majors": {"companies": {"XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips"}, "description": "Largest diversified energy companies with global E&P, refining, and chemicals."},
                    "European Majors": {"companies": {"SHEL": "Shell", "BP": "BP", "TTE": "TotalEnergies"}, "description": "Global integrated energy companies based in Europe with large transition investments."},
                },
            },
            "Exploration & Production": {
                "description": "Pure-play upstream oil and gas producers.",
                "theme": "Shale efficiency gains and Permian consolidation driving cost curve improvements.",
                "market_size": "$500B+ market cap",
                "sub_industries": {
                    "Shale / Permian": {"companies": {"PXD": "Pioneer", "FANG": "Diamondback", "MPC": "Marathon"}, "description": "U.S. unconventional oil producers focused on the Permian Basin and other shale plays."},
                },
            },
        },
    },
    "Consumer Disc.": {
        "etf": "XLY",
        "description": "Companies selling non-essential goods and services — retail, autos, travel, media, and restaurants.",
        "industries": {
            "E-Commerce & Retail": {
                "description": "Online and omnichannel retail platforms.",
                "theme": "Amazon dominance; international e-commerce growth; AI-driven personalization.",
                "market_size": "$5T+ global e-commerce",
                "sub_industries": {
                    "E-Commerce Platforms": {"companies": {"AMZN": "Amazon", "BABA": "Alibaba", "SHOP": "Shopify"}, "description": "Online marketplaces and commerce infrastructure providers."},
                    "Specialty Retail": {"companies": {"NKE": "Nike", "TJX": "TJX", "LULU": "Lululemon"}, "description": "Brand-driven specialty retailers across apparel, footwear, and lifestyle."},
                },
            },
            "Autos & EVs": {
                "description": "Traditional automakers and electric vehicle manufacturers.",
                "theme": "EV adoption pace, China competition, and margin pressure dominating narratives.",
                "market_size": "$3T+ global auto market",
                "sub_industries": {
                    "Electric Vehicles": {"companies": {"TSLA": "Tesla", "RIVN": "Rivian", "GM": "GM EV"}, "description": "Pure-play and incumbent EV manufacturers competing for market share."},
                    "Traditional Autos": {"companies": {"F": "Ford", "GM": "General Motors", "TM": "Toyota"}, "description": "Legacy automakers managing ICE profitability while investing in EVs."},
                },
            },
        },
    },
    "Consumer Staples": {
        "etf": "XLP",
        "description": "Companies producing essential consumer goods — food, beverages, household products, and personal care.",
        "industries": {
            "Food & Beverage": {
                "description": "Packaged food, beverages, and consumer staples brands.",
                "theme": "Volume recovery after price-driven growth; GLP-1 headwinds to snack/food volumes.",
                "market_size": "$3T+ global market",
                "sub_industries": {
                    "Beverages": {"companies": {"KO": "Coca-Cola", "PEP": "PepsiCo", "MNST": "Monster"}, "description": "Carbonated soft drinks, energy drinks, water, and other non-alcoholic beverages."},
                    "Packaged Foods": {"companies": {"MDLZ": "Mondelez", "GIS": "General Mills", "CPB": "Campbell"}, "description": "Shelf-stable branded food products sold through grocery and mass retail channels."},
                },
            },
            "Household Products": {
                "description": "Cleaning, personal care, and hygiene product manufacturers.",
                "theme": "Private label competition and commodity cost normalization.",
                "market_size": "$500B+",
                "sub_industries": {
                    "Diversified HPC": {"companies": {"PG": "Procter & Gamble", "CLX": "Clorox", "CHD": "Church & Dwight"}, "description": "Diversified household and personal care brands sold globally through mass retail."},
                },
            },
        },
    },
    "Industrials": {
        "etf": "XLI",
        "description": "Aerospace, defense, transportation, machinery, and industrial conglomerates.",
        "industries": {
            "Aerospace & Defense": {
                "description": "Military and commercial aircraft, defense systems, and space.",
                "theme": "Defense budget growth globally; commercial aviation recovery and backlog execution.",
                "market_size": "$1T+",
                "sub_industries": {
                    "Defense Primes": {"companies": {"LMT": "Lockheed Martin", "RTX": "RTX", "NOC": "Northrop"}, "description": "Major defense contractors for aircraft, missiles, and defense systems."},
                    "Commercial Aviation": {"companies": {"BA": "Boeing", "AIR.PA": "Airbus", "GE": "GE Aerospace"}, "description": "Commercial aircraft manufacturers and jet engine producers."},
                },
            },
            "Transportation": {
                "description": "Rail, trucking, logistics, and freight.",
                "theme": "Freight cycle recovery; nearshoring driving rail volume growth.",
                "market_size": "$500B+",
                "sub_industries": {
                    "Railroads": {"companies": {"UNP": "Union Pacific", "CSX": "CSX", "NSC": "Norfolk Southern"}, "description": "Class I railroads transporting freight across North America."},
                    "Trucking & Logistics": {"companies": {"UPS": "UPS", "FDX": "FedEx", "ODFL": "Old Dominion"}, "description": "Parcel delivery, LTL, and freight logistics."},
                },
            },
        },
    },
    "Utilities": {
        "etf": "XLU",
        "description": "Electric, gas, and water utilities providing essential services with regulated returns.",
        "industries": {
            "Electric Utilities": {
                "description": "Regulated and independent power producers distributing electricity.",
                "theme": "AI data center power demand creating unprecedented load growth for utilities.",
                "market_size": "$1T+",
                "sub_industries": {
                    "Regulated Electric": {"companies": {"NEE": "NextEra", "SO": "Southern Co", "DUK": "Duke Energy"}, "description": "Regulated electric utilities earning allowed returns on their rate base."},
                    "Independent Power": {"companies": {"VST": "Vistra", "CEG": "Constellation", "NRG": "NRG Energy"}, "description": "Merchant power generators selling electricity at market prices."},
                },
            },
        },
    },
    "Real Estate": {
        "etf": "XLRE",
        "description": "Real estate investment trusts (REITs) owning commercial, residential, industrial, and specialty properties.",
        "industries": {
            "Data Center REITs": {
                "description": "REITs owning and leasing data center facilities to cloud providers and enterprises.",
                "theme": "AI-driven hyperscaler demand driving record pre-leasing and rent growth.",
                "market_size": "$200B+",
                "sub_industries": {
                    "Hyperscale Data Centers": {"companies": {"EQIX": "Equinix", "DLR": "Digital Realty", "AMT": "American Tower"}, "description": "Colocation and wholesale data center operators serving cloud providers."},
                },
            },
            "Industrial REITs": {
                "description": "Warehouses, logistics centers, and distribution facilities.",
                "theme": "E-commerce demand and nearshoring supply chain build-out driving occupancy.",
                "market_size": "$150B+",
                "sub_industries": {
                    "Logistics & Warehousing": {"companies": {"PLD": "Prologis", "REXR": "Rexford", "EGP": "EastGroup"}, "description": "Last-mile and bulk distribution warehouse operators."},
                },
            },
        },
    },
    "Materials": {
        "etf": "XLB",
        "description": "Mining, metals, chemicals, and forest products companies.",
        "industries": {
            "Metals & Mining": {
                "description": "Extraction and processing of metals including copper, gold, lithium, and steel.",
                "theme": "Copper demand for electrification; lithium cycle; gold as inflation hedge.",
                "market_size": "$1T+",
                "sub_industries": {
                    "Copper": {"companies": {"FCX": "Freeport-McMoRan", "SCCO": "Southern Copper"}, "description": "Primary copper producers benefiting from electrification megatrend demand."},
                    "Gold & Precious Metals": {"companies": {"NEM": "Newmont", "GOLD": "Barrick", "AEM": "Agnico Eagle"}, "description": "Gold miners producing bullion as an inflation and safe-haven asset."},
                    "Lithium": {"companies": {"ALB": "Albemarle", "SQM": "SQM", "LTHM": "Livent"}, "description": "Lithium chemical producers supplying EV battery manufacturers."},
                },
            },
        },
    },
    "Comm. Services": {
        "etf": "XLC",
        "description": "Media, entertainment, telecommunications, and interactive digital platforms.",
        "industries": {
            "Interactive Media": {
                "description": "Social media, search, and digital advertising platforms.",
                "theme": "AI-enhanced ad targeting driving revenue re-acceleration after 2022 downturn.",
                "market_size": "$3T+",
                "sub_industries": {
                    "Social Media": {"companies": {"META": "Meta", "SNAP": "Snap", "PINS": "Pinterest"}, "description": "Social networking platforms monetized primarily through digital advertising."},
                    "Search & AI": {"companies": {"GOOGL": "Alphabet", "MSFT": "Microsoft Bing"}, "description": "Search engines and AI assistants capturing intent-based advertising revenue."},
                },
            },
            "Telecom": {
                "description": "Wireless and wireline telecommunications service providers.",
                "theme": "5G monetization; fiber buildout; ARPU growth through bundling.",
                "market_size": "$1T+",
                "sub_industries": {
                    "Wireless Carriers": {"companies": {"VZ": "Verizon", "T": "AT&T", "TMUS": "T-Mobile"}, "description": "Mobile network operators providing wireless voice and data services."},
                },
            },
        },
    },
}

# Key companies with full profiles
COMPANY_PROFILES = {
    "NVDA": {
        "name": "NVIDIA Corporation",
        "ticker": "NVDA",
        "sector": "Technology",
        "industry": "Semiconductors",
        "sub_industry": "GPU & AI Accelerators",
        "description": "NVIDIA designs and sells graphics processing units (GPUs), system-on-chip units, and now dominates the AI accelerator market with its H100/H200/B200 data center GPUs.",
        "segments": ["Data Center", "Gaming", "Professional Visualization", "Automotive", "OEM & Other"],
        "competitors": ["AMD", "INTC", "GOOGL", "AMZN", "MSFT"],
        "key_customers": ["Microsoft", "Amazon", "Google", "Meta", "Tesla"],
        "moat": "CUDA software ecosystem creates an enormous switching cost. Developers write AI code in CUDA — switching to AMD or custom chips requires significant re-engineering. This software moat reinforces the hardware dominance.",
        "bull_case": "AI infrastructure spend is still in early innings. Hyperscaler capex guidance points to $300B+ in 2025. NVIDIA captures ~80% of AI training compute. Blackwell ramp adds incremental revenue far above consensus estimates.",
        "bear_case": "Customer concentration risk — 5 hyperscalers represent ~50% of revenue. Custom ASIC chips from Google (TPU), Amazon (Trainium), and Microsoft (Maia) could reduce dependence on NVIDIA over time. Export restrictions to China removed a high-margin market.",
        "catalysts": ["Blackwell GPU ramp", "Sovereign AI demand", "Edge AI expansion", "CUDA ecosystem moat deepening"],
        "risks": ["Export controls", "Customer ASICs", "Valuation at 35x forward earnings", "Supply chain constraints"],
    },
    "AAPL": {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Technology",
        "industry": "Hardware & Networking",
        "sub_industry": "Consumer Electronics",
        "description": "Apple designs, manufactures, and sells consumer electronics including iPhone, Mac, iPad, and wearables, and operates a high-margin services ecosystem (App Store, iCloud, Apple Pay, Apple TV+).",
        "segments": ["iPhone", "Mac", "iPad", "Wearables Home & Accessories", "Services"],
        "competitors": ["GOOGL", "MSFT", "005930.KS", "META"],
        "key_customers": ["Consumer (direct)", "Enterprise", "Education"],
        "moat": "Ecosystem lock-in through iOS, iCloud, and App Store creates high switching costs. Services business generates ~$100B annually with 70%+ gross margins, providing a durable recurring revenue stream.",
        "bull_case": "Apple Intelligence (on-device AI) drives an iPhone upgrade supercycle. Services revenue approaching $100B. India manufacturing diversification reduces China risk. Installed base of 2B+ active devices.",
        "bear_case": "China revenue (~20% of total) at risk from geopolitical tensions. Hardware price increases risk demand elasticity. AI features may not be sufficient to drive upgrades. Services facing regulatory scrutiny.",
        "catalysts": ["Apple Intelligence AI features", "India manufacturing scale", "Vision Pro ecosystem", "Financial services expansion"],
        "risks": ["China geopolitics", "Hardware price increases", "EU regulatory pressure", "Antitrust App Store rulings"],
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
        "sector": "Technology",
        "industry": "Software",
        "sub_industry": "Cloud Platforms",
        "description": "Microsoft operates Azure cloud platform, Office 365 productivity suite, LinkedIn, Xbox gaming, and GitHub. The company is deeply integrated into enterprise AI through its $13B OpenAI partnership.",
        "segments": ["Productivity & Business Processes", "Intelligent Cloud", "More Personal Computing"],
        "competitors": ["AMZN", "GOOGL", "CRM", "ORCL"],
        "key_customers": ["Enterprise", "Government", "SMB", "Developers"],
        "moat": "Deeply embedded in enterprise workflows through Office 365, Teams, and Azure Active Directory. GitHub dominates developer infrastructure. OpenAI partnership provides frontier AI model access.",
        "bull_case": "Copilot AI assistant monetization at $30/seat/month represents a massive TAM expansion across 400M Office seats. Azure AI services re-accelerating cloud growth. GitHub Copilot adoption compounding.",
        "bear_case": "Azure growth deceleration relative to AWS. OpenAI investment requires ongoing capital commitment. Antitrust scrutiny on gaming/Activision integration. AI CapEx weighing on free cash flow.",
        "catalysts": ["Copilot seat expansion", "Azure AI re-acceleration", "GitHub Copilot monetization", "EU AI Act compliance advantage"],
        "risks": ["AWS competitive pressure", "OpenAI dependency", "Antitrust", "CapEx intensity"],
    },
    "TSM": {
        "name": "Taiwan Semiconductor Manufacturing Company",
        "ticker": "TSM",
        "sector": "Technology",
        "industry": "Semiconductors",
        "sub_industry": "Foundries",
        "description": "TSMC is the world's largest and most advanced contract semiconductor manufacturer, producing chips for Apple, NVIDIA, AMD, Qualcomm, and virtually every major fabless chip designer at leading-edge nodes.",
        "segments": ["Advanced Nodes (≤7nm)", "Specialty Technology", "Advanced Packaging"],
        "competitors": ["Samsung Foundry", "Intel Foundry", "GlobalFoundries"],
        "key_customers": ["Apple", "NVIDIA", "AMD", "Qualcomm", "Broadcom"],
        "moat": "Process technology leadership at 3nm and 2nm — only Samsung is remotely competitive but 1-2 generations behind. TSMC's manufacturing expertise is the result of decades of compounding learning. Switching costs are effectively infinite for leading-edge designs.",
        "bull_case": "AI chip demand creating multi-year capex cycle. CoWoS advanced packaging capacity is structurally undersupplied vs. demand from NVIDIA and Apple. Arizona fabs reduce geopolitical discount on valuation.",
        "bear_case": "Taiwan geopolitical risk is the single largest overhang — a conflict scenario is a tail risk with no mitigation. Customer concentration in Apple (~25% of revenue).",
        "catalysts": ["N2 (2nm) ramp", "CoWoS packaging expansion", "Arizona fab economics improvement", "AI chip demand multi-year tailwind"],
        "risks": ["Taiwan geopolitics", "Apple concentration", "CapEx intensity", "China export controls on equipment"],
    },
    "LLY": {
        "name": "Eli Lilly and Company",
        "ticker": "LLY",
        "sector": "Healthcare",
        "industry": "Pharmaceuticals",
        "sub_industry": "Obesity/GLP-1",
        "description": "Eli Lilly develops and commercializes branded pharmaceuticals, most notably Mounjaro/Zepbound (tirzepatide) for diabetes and obesity, and Kisunla for Alzheimer's disease.",
        "segments": ["Diabetes", "Obesity", "Oncology", "Neuroscience", "Immunology"],
        "competitors": ["NVO", "PFE", "AZN", "MRK"],
        "key_customers": ["Patients (via PBMs and payers)", "Hospital systems", "Government healthcare programs"],
        "moat": "Tirzepatide's dual GIP/GLP-1 mechanism demonstrates superior weight loss vs. Novo's semaglutide in head-to-head trials. Manufacturing scale-up is the primary constraint — and Lilly is investing $20B+ in manufacturing capacity.",
        "bull_case": "GLP-1 obesity market could reach $150B by 2030. Tirzepatide's superior efficacy positions Lilly for market share leadership. Pipeline in Alzheimer's (donanemab) and oncology adds multiple shots on goal.",
        "bear_case": "Novo Nordisk's semaglutide remains the market leader with entrenched prescribing habits. Manufacturing capacity constraints limit revenue upside. Payer pushback on obesity drug coverage.",
        "catalysts": ["Obesity drug volume acceleration", "Alzheimer's drug launch", "Manufacturing capacity expansion", "Oral GLP-1 program progress"],
        "risks": ["Competition from Novo Nordisk", "Payer/coverage restrictions", "Manufacturing execution", "Pricing reform risk"],
    },
    "JPM": {
        "name": "JPMorgan Chase & Co.",
        "ticker": "JPM",
        "sector": "Financials",
        "industry": "Banks",
        "sub_industry": "Money Center Banks",
        "description": "JPMorgan Chase is the largest U.S. bank by assets (~$4T), operating across consumer banking, commercial banking, investment banking, asset management, and payments.",
        "segments": ["Consumer & Community Banking", "Commercial Banking", "Corporate & Investment Bank", "Asset & Wealth Management"],
        "competitors": ["BAC", "C", "GS", "MS", "WFC"],
        "key_customers": ["Consumers", "Corporations", "Institutional investors", "Governments"],
        "moat": "Scale advantages in technology investment ($15B+ tech budget), global distribution, and brand trust. #1 position in investment banking, credit cards, and commercial banking creates durable competitive advantages.",
        "bull_case": "Normalized rate environment supports net interest income. Investment banking fee recovery as M&A and IPO markets reopen. AI-driven efficiency improvements across the bank. Capital return through buybacks.",
        "bear_case": "Net interest margin compression if Fed cuts rates aggressively. Credit quality normalization from pandemic-era lows. Regulatory capital requirements (Basel III endgame) could constrain returns.",
        "catalysts": ["M&A cycle recovery", "Net interest income stability", "Wealth management AUM growth", "International expansion"],
        "risks": ["Rate cuts compressing NIM", "Credit cycle normalization", "Regulatory capital requirements", "Geopolitical credit exposure"],
    },
    "AMZN": {
        "name": "Amazon.com, Inc.",
        "ticker": "AMZN",
        "sector": "Consumer Disc.",
        "industry": "E-Commerce & Retail",
        "sub_industry": "E-Commerce Platforms",
        "description": "Amazon operates e-commerce, Amazon Web Services (AWS), advertising, Prime membership, Alexa, and fulfillment logistics — the most diversified technology and retail conglomerate.",
        "segments": ["AWS", "Advertising", "Third-Party Seller Services", "Online Stores", "Physical Stores", "Subscription Services"],
        "competitors": ["MSFT", "GOOGL", "WMT", "SHOP"],
        "key_customers": ["Consumers", "SMBs (AWS & marketplace)", "Enterprises (AWS)", "Advertisers"],
        "moat": "AWS is the global cloud market leader with deep enterprise customer relationships. Prime membership creates habitual buying with 200M+ global subscribers. Advertising business growing at 20%+ with unique purchase-intent data.",
        "bull_case": "AWS re-acceleration from AI workloads. Advertising approaching $60B run rate with high margins. Operating leverage across fulfillment network. Grocery and healthcare expansion.",
        "bear_case": "AWS faces intensifying competition from Azure and GCP. Antitrust scrutiny on marketplace practices. CapEx intensity for AI and fulfillment weighing on free cash flow.",
        "catalysts": ["AWS AI services revenue", "Advertising growth", "Operating margin expansion", "Healthcare (One Medical/RxPass)"],
        "risks": ["Antitrust actions", "AWS competition", "Consumer spending slowdown", "CapEx requirement"],
    },
    "XOM": {
        "name": "Exxon Mobil Corporation",
        "ticker": "XOM",
        "sector": "Energy",
        "industry": "Integrated Oil & Gas",
        "sub_industry": "Oil Majors",
        "description": "ExxonMobil is the largest U.S. oil and gas company by market cap, operating across upstream E&P (Permian, Guyana), refining/chemicals, and low-carbon solutions.",
        "segments": ["Upstream", "Energy Products (Refining)", "Chemical Products", "Specialty Products", "Low Carbon Solutions"],
        "competitors": ["CVX", "SHEL", "BP", "TTE", "COP"],
        "key_customers": ["Refiners", "Industrial customers", "Petrochemical companies", "End consumers"],
        "moat": "Low-cost Permian and Guyana production assets. Pioneer Natural Resources acquisition makes Exxon the dominant Permian operator. Chemical business provides earnings diversification.",
        "bull_case": "Guyana low-cost barrels ramping. Pioneer acquisition synergies. Structural oil demand from emerging markets. Capital discipline driving shareholder returns.",
        "bear_case": "Oil price sensitivity — every $10/bbl move affects earnings significantly. Energy transition accelerating faster than expected. Permian acquisition debt load.",
        "catalysts": ["Guyana ramp-up", "Pioneer synergies", "Chemical margin recovery", "Low-carbon business revenue"],
        "risks": ["Oil price decline", "Energy transition", "Permian acquisition integration", "Regulatory carbon costs"],
    },
}

# ═════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)
def get_stock_data(ticker: str) -> dict:
    """Fetch key financials and price data for a company."""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        hist = t.history(period="1y")
        week_chg = None
        if len(hist) >= 6:
            week_chg = round((hist["Close"].iloc[-1] - hist["Close"].iloc[-6]) / hist["Close"].iloc[-6] * 100, 2)
        elif len(hist) >= 2:
            week_chg = round((hist["Close"].iloc[-1] - hist["Close"].iloc[-2]) / hist["Close"].iloc[-2] * 100, 2)
        return {
            "price":       round(info.get("currentPrice") or info.get("regularMarketPrice") or (hist["Close"].iloc[-1] if not hist.empty else 0), 2),
            "mktcap":      info.get("marketCap", 0),
            "pe":          info.get("forwardPE") or info.get("trailingPE"),
            "revenue":     info.get("totalRevenue"),
            "gross_margin":info.get("grossMargins"),
            "op_margin":   info.get("operatingMargins"),
            "week_chg":    week_chg,
            "52w_high":    info.get("fiftyTwoWeekHigh"),
            "52w_low":     info.get("fiftyTwoWeekLow"),
            "hist":        hist,
            "name":        info.get("shortName", ticker),
        }
    except Exception:
        return {}


def fmt_mktcap(v):
    if not v: return "N/A"
    if v >= 1e12: return f"${v/1e12:.1f}T"
    if v >= 1e9:  return f"${v/1e9:.1f}B"
    return f"${v/1e6:.0f}M"


def pct_color(val):
    if val is None or val == "N/A": return SILVER
    try:
        v = float(str(val).replace("%","").replace("+",""))
        return GREEN if v >= 0 else RED
    except: return SILVER


def section(title):
    st.markdown(f'<div style="font-size:11px;font-weight:700;letter-spacing:0.14em;'
                f'text-transform:uppercase;color:{GOLD};border-bottom:1px solid {SLATE};'
                f'padding-bottom:7px;margin:20px 0 12px">{title}</div>',
                unsafe_allow_html=True)


def card_md(label, value, delta=None, sub=None):
    delta_html = ""
    if delta is not None:
        clr = GREEN if (isinstance(delta, (int,float)) and delta >= 0) else RED
        arrow = "▲" if (isinstance(delta, (int,float)) and delta >= 0) else "▼"
        delta_html = f'<div style="color:{clr};font-size:12px;font-weight:600;margin-top:3px">{arrow} {abs(delta) if isinstance(delta,(int,float)) else delta}</div>'
    sub_html = f'<div style="color:{SILVER};font-size:10px;margin-top:2px">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;padding:14px 16px;margin-bottom:8px">
        <div style="font-size:10px;letter-spacing:0.09em;text-transform:uppercase;color:{SILVER};margin-bottom:4px">{label}</div>
        <div style="font-size:22px;font-weight:700;color:{WHITE}">{value}</div>
        {delta_html}{sub_html}
    </div>""", unsafe_allow_html=True)


def breadcrumb(path: list):
    """Render clickable breadcrumb navigation."""
    parts = []
    for i, (label, state) in enumerate(path):
        if i < len(path) - 1:
            parts.append(f'<span style="color:{GOLD};cursor:pointer" '
                        f'onclick="void(0)">{label}</span>'
                        f'<span style="color:{SILVER};margin:0 6px">›</span>')
        else:
            parts.append(f'<span style="color:{WHITE};font-weight:600">{label}</span>')

    st.markdown(
        f'<div style="font-size:12px;margin-bottom:16px;padding:8px 12px;'
        f'background:{CARD};border-radius:6px;border-left:2px solid {GOLD}">'
        + "".join(parts) + '</div>',
        unsafe_allow_html=True,
    )


def mini_sparkline_dd(hist, color=GREEN):
    if hist is None or len(hist) < 5:
        return None
    series = hist["Close"].tail(30)
    fig = go.Figure(go.Scatter(
        x=list(range(len(series))), y=series.values,
        mode="lines", line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=60, showlegend=False, margin=dict(l=0,r=0,t=0,b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def ai_commentary(prompt_text: str, cache_key: str) -> str:
    """Generate AI market commentary via Claude API."""
    if cache_key in st.session_state.get("ai_cache", {}):
        return st.session_state["ai_cache"][cache_key]
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 600,
                  "messages": [{"role": "user", "content": prompt_text}]},
            timeout=20,
        )
        if r.status_code == 200:
            text = r.json()["content"][0]["text"].strip()
            if "ai_cache" not in st.session_state:
                st.session_state["ai_cache"] = {}
            st.session_state["ai_cache"][cache_key] = text
            return text
    except Exception:
        pass
    return ""

# ═════════════════════════════════════════════════════════════════════════════
# VIEW: SECTOR
# ═════════════════════════════════════════════════════════════════════════════

def render_sector_view(sector_name: str, sec_week_chg: float):
    sector = TAXONOMY.get(sector_name, {})
    industries = sector.get("industries", {})

    breadcrumb([("Market", None), (sector_name, None)])

    # Header
    chg_clr = GREEN if (sec_week_chg or 0) >= 0 else RED
    st.markdown(f"""
    <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;
                padding:20px 24px;margin-bottom:16px">
        <div style="font-size:22px;font-weight:800;color:{WHITE}">{sector_name}</div>
        <div style="font-size:13px;color:{TEXT};margin-top:6px">{sector.get('description','')}</div>
        <div style="margin-top:10px">
            <span style="color:{chg_clr};font-size:16px;font-weight:700">
                {'▲' if (sec_week_chg or 0)>=0 else '▼'} {abs(sec_week_chg or 0):.2f}% this week
            </span>
            <span style="color:{SILVER};font-size:11px;margin-left:12px">
                ETF: {sector.get('etf','')}
            </span>
        </div>
    </div>""", unsafe_allow_html=True)

    section(f"Industries within {sector_name}")

    # Industry cards — clickable
    for ind_name, ind_data in industries.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;
                        padding:14px 18px;margin-bottom:8px">
                <div style="font-size:14px;font-weight:700;color:{WHITE}">{ind_name}</div>
                <div style="font-size:11px;color:{TEXT};margin-top:4px">{ind_data.get('description','')}</div>
                <div style="font-size:10px;color:{GOLD};margin-top:6px">
                    🎯 Theme: {ind_data.get('theme','')}
                </div>
                <div style="font-size:10px;color:{SILVER};margin-top:3px">
                    Market size: {ind_data.get('market_size','N/A')} &nbsp;·&nbsp;
                    Sub-industries: {len(ind_data.get('sub_industries',{}))}
                </div>
            </div>""", unsafe_allow_html=True)
        with col2:
            if st.button(f"Explore →", key=f"ind_{sector_name}_{ind_name}"):
                st.session_state["drill_level"] = "industry"
                st.session_state["drill_sector"] = sector_name
                st.session_state["drill_industry"] = ind_name
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# VIEW: INDUSTRY
# ═════════════════════════════════════════════════════════════════════════════

def render_industry_view(sector_name: str, industry_name: str):
    sector   = TAXONOMY.get(sector_name, {})
    industry = sector.get("industries", {}).get(industry_name, {})
    sub_inds = industry.get("sub_industries", {})

    breadcrumb([
        ("Market", None),
        (sector_name, "sector"),
        (industry_name, None),
    ])

    # Back button
    if st.button("← Back to Sector"):
        st.session_state["drill_level"] = "sector"
        st.rerun()

    # Header
    st.markdown(f"""
    <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;
                padding:20px 24px;margin-bottom:16px">
        <div style="font-size:10px;color:{SILVER};letter-spacing:0.1em;text-transform:uppercase">{sector_name}</div>
        <div style="font-size:22px;font-weight:800;color:{WHITE};margin-top:4px">{industry_name}</div>
        <div style="font-size:13px;color:{TEXT};margin-top:6px">{industry.get('description','')}</div>
        <div style="margin-top:10px;padding:8px 12px;background:{NAVY};border-radius:6px">
            <span style="color:{GOLD};font-size:11px;font-weight:700">INVESTMENT THEME: </span>
            <span style="color:{TEXT};font-size:11px">{industry.get('theme','')}</span>
        </div>
        <div style="margin-top:8px">
            <span style="color:{SILVER};font-size:11px">Market Size: </span>
            <span style="color:{WHITE};font-size:11px;font-weight:600">{industry.get('market_size','N/A')}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # AI Commentary
    with st.expander("🤖 AI Industry Analysis", expanded=False):
        with st.spinner("Generating analysis..."):
            commentary = ai_commentary(
                f"Write a 3-4 sentence professional institutional analyst commentary on the {industry_name} industry within {sector_name}. "
                f"Cover: current investment theme ({industry.get('theme','')}), key drivers, risks, and what investors are watching. "
                f"Sound like Goldman Sachs research, not generic AI. Be specific and data-driven.",
                f"industry_{sector_name}_{industry_name}"
            )
        if commentary:
            st.markdown(f'<div style="font-size:13px;color:{TEXT};line-height:1.7">{commentary}</div>',
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:13px;color:{TEXT};line-height:1.7">'
                       f'The {industry_name} industry is experiencing significant shifts driven by {industry.get("theme","evolving market dynamics")}. '
                       f'Market size is estimated at {industry.get("market_size","N/A")} with {'growing' if True else 'stable'} competitive dynamics. '
                       f'Investors are monitoring segment-level performance and company-specific execution.</div>',
                       unsafe_allow_html=True)

    section("Segments / Sub-Industries")

    for sub_name, sub_data in sub_inds.items():
        companies = sub_data.get("companies", {})
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            company_tags = " &nbsp;·&nbsp; ".join(
                f'<span style="color:{GOLD}">{name}</span>' for ticker, name in list(companies.items())[:4]
            )
            st.markdown(f"""
            <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;
                        padding:12px 16px;margin-bottom:6px">
                <div style="font-size:13px;font-weight:700;color:{WHITE}">{sub_name}</div>
                <div style="font-size:11px;color:{TEXT};margin-top:3px">{sub_data.get('description','')}</div>
                <div style="font-size:10px;margin-top:6px">{company_tags}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="padding-top:12px;font-size:11px;color:{SILVER}">{len(companies)} companies</div>', unsafe_allow_html=True)
        with col3:
            if st.button("Explore →", key=f"sub_{sector_name}_{industry_name}_{sub_name}"):
                st.session_state["drill_level"] = "sub_industry"
                st.session_state["drill_sub_industry"] = sub_name
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# VIEW: SUB-INDUSTRY
# ═════════════════════════════════════════════════════════════════════════════

def render_sub_industry_view(sector_name, industry_name, sub_industry_name):
    sub = TAXONOMY.get(sector_name,{}).get("industries",{}).get(industry_name,{}).get("sub_industries",{}).get(sub_industry_name,{})
    companies = sub.get("companies", {})

    breadcrumb([
        ("Market", None), (sector_name, "sector"),
        (industry_name, "industry"), (sub_industry_name, None),
    ])

    col_back1, col_back2 = st.columns(2)
    with col_back1:
        if st.button("← Back to Industry"):
            st.session_state["drill_level"] = "industry"
            st.rerun()

    st.markdown(f"""
    <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;padding:20px 24px;margin-bottom:16px">
        <div style="font-size:10px;color:{SILVER};letter-spacing:0.1em;text-transform:uppercase">{sector_name} › {industry_name}</div>
        <div style="font-size:22px;font-weight:800;color:{WHITE};margin-top:4px">{sub_industry_name}</div>
        <div style="font-size:13px;color:{TEXT};margin-top:6px">{sub.get('description','')}</div>
    </div>""", unsafe_allow_html=True)

    with st.expander("🤖 AI Sub-Industry Analysis", expanded=False):
        with st.spinner("Generating..."):
            txt = ai_commentary(
                f"Write 3-4 sentences of institutional-quality analyst commentary on the {sub_industry_name} segment within {industry_name} ({sector_name}). "
                f"Be specific: current dynamics, key drivers, competitive landscape, and investor focus. "
                f"Companies include: {', '.join(companies.values())}. Sound like Morgan Stanley research.",
                f"sub_{sector_name}_{industry_name}_{sub_industry_name}"
            )
        st.markdown(f'<div style="font-size:13px;color:{TEXT};line-height:1.7">{txt or "Analysis unavailable — check API connectivity."}</div>', unsafe_allow_html=True)

    section(f"Companies in {sub_industry_name}")

    cols = st.columns(3)
    for i, (ticker, company_name) in enumerate(companies.items()):
        with cols[i % 3]:
            data = get_stock_data(ticker)
            wk   = data.get("week_chg")
            clr  = GREEN if (wk or 0) >= 0 else RED
            st.markdown(f"""
            <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;padding:14px;margin-bottom:8px">
                <div style="font-size:10px;color:{SILVER};letter-spacing:0.08em">{ticker}</div>
                <div style="font-size:15px;font-weight:700;color:{WHITE};margin-top:2px">{company_name}</div>
                <div style="font-size:20px;font-weight:700;color:{WHITE};margin-top:4px">${data.get('price','N/A'):,.2f}</div>
                <div style="color:{clr};font-size:12px;font-weight:600;margin-top:2px">
                    {'▲' if (wk or 0)>=0 else '▼'} {abs(wk or 0):.2f}% this week
                </div>
                <div style="color:{SILVER};font-size:10px;margin-top:4px">
                    Mkt Cap: {fmt_mktcap(data.get('mktcap'))} &nbsp;·&nbsp;
                    Fwd P/E: {f"{data.get('pe'):.1f}x" if data.get('pe') else 'N/A'}
                </div>
            </div>""", unsafe_allow_html=True)
            sp = mini_sparkline_dd(data.get("hist"), color=clr)
            if sp:
                st.plotly_chart(sp, use_container_width=True, config={"displayModeBar": False})
            if st.button(f"Deep Dive: {ticker}", key=f"co_{ticker}_{sub_industry_name}"):
                st.session_state["drill_level"] = "company"
                st.session_state["drill_ticker"] = ticker
                st.session_state["drill_company_name"] = company_name
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# VIEW: COMPANY
# ═════════════════════════════════════════════════════════════════════════════

def render_company_view(ticker: str, company_display_name: str):
    profile = COMPANY_PROFILES.get(ticker, {})
    data    = get_stock_data(ticker)
    name    = profile.get("name", company_display_name)

    breadcrumb([
        ("Market", None),
        (profile.get("sector",""), "sector"),
        (profile.get("industry",""), "industry"),
        (profile.get("sub_industry",""), "sub_industry"),
        (name, None),
    ])

    if st.button("← Back to Companies"):
        st.session_state["drill_level"] = "sub_industry"
        st.rerun()

    # ── Header ────────────────────────────────────────────────────────────────
    wk  = data.get("week_chg")
    clr = GREEN if (wk or 0) >= 0 else RED
    st.markdown(f"""
    <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;padding:20px 24px;margin-bottom:16px">
        <div style="font-size:11px;color:{SILVER};letter-spacing:0.1em;text-transform:uppercase">{ticker} · {profile.get('sector','')} › {profile.get('industry','')}</div>
        <div style="font-size:26px;font-weight:800;color:{WHITE};margin-top:4px">{name}</div>
        <div style="display:flex;gap:24px;margin-top:12px;flex-wrap:wrap">
            <div>
                <div style="font-size:28px;font-weight:800;color:{WHITE}">${data.get('price',0):,.2f}</div>
                <div style="color:{clr};font-size:13px;font-weight:600">{'▲' if (wk or 0)>=0 else '▼'} {abs(wk or 0):.2f}% this week</div>
            </div>
            <div style="color:{SILVER};font-size:11px;line-height:2">
                Market Cap: <b style="color:{WHITE}">{fmt_mktcap(data.get('mktcap'))}</b><br>
                Fwd P/E: <b style="color:{WHITE}">{f"{data.get('pe'):.1f}x" if data.get('pe') else 'N/A'}</b><br>
                Gross Margin: <b style="color:{WHITE}">{f"{data.get('gross_margin',0)*100:.1f}%" if data.get('gross_margin') else 'N/A'}</b>
            </div>
            <div style="color:{SILVER};font-size:11px;line-height:2">
                52W High: <b style="color:{WHITE}">${data.get('52w_high',0):,.2f}</b><br>
                52W Low: <b style="color:{WHITE}">${data.get('52w_low',0):,.2f}</b><br>
                Op. Margin: <b style="color:{WHITE}">{f"{data.get('op_margin',0)*100:.1f}%" if data.get('op_margin') else 'N/A'}</b>
            </div>
        </div>
        <div style="font-size:12px;color:{TEXT};margin-top:12px;line-height:1.6">{profile.get('description','')}</div>
    </div>""", unsafe_allow_html=True)

    # ── Price chart ───────────────────────────────────────────────────────────
    hist = data.get("hist")
    if hist is not None and len(hist) > 5:
        fig = go.Figure(go.Scatter(
            x=hist.index, y=hist["Close"],
            mode="lines", line=dict(color=clr, width=2),
            fill="tozeroy",
            fillcolor=f"rgba({int(clr[1:3],16)},{int(clr[3:5],16)},{int(clr[5:7],16)},0.08)",
            hovertemplate="$%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=200, showlegend=False,
            margin=dict(l=8,r=8,t=10,b=8),
            xaxis=dict(showgrid=False, color=SILVER, tickfont=dict(size=9)),
            yaxis=dict(gridcolor=SLATE, color=SILVER, tickfont=dict(size=9), tickprefix="$"),
            font=dict(color=WHITE),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Business", "🎯 Investment Thesis", "🏆 Competitive Position", "🔗 Related Companies"])

    with tab1:
        section("Business Segments")
        segs = profile.get("segments", [])
        if segs:
            cols = st.columns(min(len(segs), 4))
            for i, seg in enumerate(segs):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div style="background:{CARD};border:1px solid {SLATE};border-radius:6px;
                                padding:10px 12px;text-align:center;margin-bottom:8px">
                        <div style="font-size:10px;color:{SILVER}">{seg}</div>
                    </div>""", unsafe_allow_html=True)

        section("Key Customers")
        customers = profile.get("key_customers", [])
        st.markdown(" &nbsp;·&nbsp; ".join(f'<span style="color:{GOLD};font-size:12px">{c}</span>' for c in customers), unsafe_allow_html=True)

    with tab2:
        section("Investment Thesis")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div style="background:{CARD};border-left:3px solid {GREEN};border-radius:6px;padding:14px 16px">
                <div style="color:{GREEN};font-size:11px;font-weight:700;letter-spacing:0.1em;margin-bottom:8px">🟢 BULL CASE</div>
                <div style="color:{TEXT};font-size:12px;line-height:1.7">{profile.get('bull_case','')}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:{CARD};border-left:3px solid {RED};border-radius:6px;padding:14px 16px">
                <div style="color:{RED};font-size:11px;font-weight:700;letter-spacing:0.1em;margin-bottom:8px">🔴 BEAR CASE</div>
                <div style="color:{TEXT};font-size:12px;line-height:1.7">{profile.get('bear_case','')}</div>
            </div>""", unsafe_allow_html=True)

        section("Catalysts & Risks")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f'<div style="font-size:11px;color:{GOLD};font-weight:700;margin-bottom:6px">KEY CATALYSTS</div>', unsafe_allow_html=True)
            for cat in profile.get("catalysts", []):
                st.markdown(f'<div style="color:{TEXT};font-size:12px;margin-bottom:4px">✅ {cat}</div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div style="font-size:11px;color:{GOLD};font-weight:700;margin-bottom:6px">KEY RISKS</div>', unsafe_allow_html=True)
            for risk in profile.get("risks", []):
                st.markdown(f'<div style="color:{TEXT};font-size:12px;margin-bottom:4px">⚠️ {risk}</div>', unsafe_allow_html=True)

        section("AI Investment Commentary")
        with st.spinner("Generating institutional commentary..."):
            ai_text = ai_commentary(
                f"Write a 4-5 sentence institutional investment commentary on {name} ({ticker}). "
                f"Cover: business quality, competitive moat, near-term catalysts ({', '.join(profile.get('catalysts',[])[:3])}), "
                f"key risks ({', '.join(profile.get('risks',[])[:3])}), and a balanced view on valuation. "
                f"Sound like CFA-level Goldman Sachs or Morgan Stanley equity research. Be specific, not generic.",
                f"company_thesis_{ticker}"
            )
        st.markdown(f'<div style="background:{CARD};border-left:3px solid {GOLD};border-radius:6px;'
                   f'padding:14px 16px;font-size:13px;color:{TEXT};line-height:1.8">'
                   f'{ai_text or profile.get("moat","Analysis unavailable.")}</div>', unsafe_allow_html=True)

    with tab3:
        section("Competitive Moat")
        st.markdown(f'<div style="background:{CARD};border-left:3px solid {BLUE};border-radius:6px;'
                   f'padding:14px 16px;font-size:13px;color:{TEXT};line-height:1.8">'
                   f'{profile.get("moat","")}</div>', unsafe_allow_html=True)

        section("Competitors")
        comp_tickers = profile.get("competitors", [])[:5]
        if comp_tickers:
            cols = st.columns(len(comp_tickers))
            for i, comp in enumerate(comp_tickers):
                with cols[i]:
                    cd = get_stock_data(comp)
                    cwk = cd.get("week_chg")
                    cclr = GREEN if (cwk or 0) >= 0 else RED
                    st.markdown(f"""
                    <div style="background:{CARD};border:1px solid {SLATE};border-radius:8px;
                                padding:12px;text-align:center;margin-bottom:8px">
                        <div style="font-size:11px;color:{SILVER}">{comp}</div>
                        <div style="font-size:16px;font-weight:700;color:{WHITE}">${cd.get('price',0):,.0f}</div>
                        <div style="color:{cclr};font-size:11px">{'▲' if (cwk or 0)>=0 else '▼'} {abs(cwk or 0):.2f}%</div>
                        <div style="color:{SILVER};font-size:9px;margin-top:3px">{fmt_mktcap(cd.get('mktcap'))}</div>
                    </div>""", unsafe_allow_html=True)
                    if st.button(f"View {comp}", key=f"comp_{ticker}_{comp}"):
                        st.session_state["drill_ticker"] = comp
                        st.session_state["drill_company_name"] = comp
                        st.session_state["drill_level"] = "company"
                        st.rerun()

    with tab4:
        section("Navigate to Related Companies")
        all_related = (profile.get("competitors",[]) + profile.get("key_customers",[]))
        known = {t: COMPANY_PROFILES[t]["name"] for t in all_related if t in COMPANY_PROFILES}
        if known:
            cols = st.columns(3)
            for i, (t, n) in enumerate(known.items()):
                with cols[i % 3]:
                    if st.button(f"🔗 {n} ({t})", key=f"rel_{ticker}_{t}"):
                        st.session_state["drill_ticker"] = t
                        st.session_state["drill_company_name"] = n
                        st.session_state["drill_level"] = "company"
                        st.rerun()
        else:
            st.markdown(f'<div style="color:{SILVER};font-size:12px">Navigate to a company via the sub-industry view to explore relationships.</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT — called from app.py
# ═════════════════════════════════════════════════════════════════════════════

def render_drilldown(sector_name: str, sec_week_chg: float):
    """Main entry point. Call this from app.py when a sector is clicked."""
    level = st.session_state.get("drill_level", "sector")

    if level == "sector":
        render_sector_view(sector_name, sec_week_chg)
    elif level == "industry":
        render_industry_view(
            st.session_state.get("drill_sector", sector_name),
            st.session_state.get("drill_industry", ""),
        )
    elif level == "sub_industry":
        render_sub_industry_view(
            st.session_state.get("drill_sector", sector_name),
            st.session_state.get("drill_industry", ""),
            st.session_state.get("drill_sub_industry", ""),
        )
    elif level == "company":
        render_company_view(
            st.session_state.get("drill_ticker", ""),
            st.session_state.get("drill_company_name", ""),
        )
