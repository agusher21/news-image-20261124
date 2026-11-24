# news-image-20261124

A newspaper-style front page capturing the world's news for **Tuesday 24 November 2026**. Built for the make.fun "news-image" bounty — one dense, legible 1024×1024 PNG with 35 stories across 7 regions, a continuous satellite arc linking the three lead illustrations ("ONE DAY, ONE ORBIT"), UTC timeline, stat strip, region tabs, and a dated DATE CHECK box naming every major event deliberately left off the page.

[![make.fun badge](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank badge](https://make.fun/badge/news-image-20261124/agusher21/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124)
[![reward badge](https://make.fun/badge/news-image-20261124/agusher21/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124)

**Pool:** $100 | **Top 50 paid** | **Entries close:** 26 Nov 2026 07:00 WIB  
**Wallet:** `7FxQ7pkQeEixkjnk6zeKPFix3KsiZWjp88VMEpTbHS8G`

## Lead stories (all dated Tue 24 Nov 2026)
1. **Nvidia / Huang** — Jensen Huang returns to HQ, shares +31.5% (best day since 2003), Nasdaq +6.5%
2. **Gaza children to Britain** — Critically injured evacuated; Israeli fire kills Palestinian; child dies of lead poisoning
3. **Space / Nuclear orbiter** — NATO chief elevates space strategy; German media: Russia may orbit nuclear spacecraft in December

## The Day in Ten (4–13)
Armenia TRIPP project & draft constitution · UN AI safety framework demand · Poland: Soviet missiles · Pakistan 4.0 quake + Lahore AQI 500+ · Nepal €1.4bn India pledge · Panama Cobre mine talks resume · Germany 450 school bomb threats · Russia Murmansk governor detained · Ex-Mossad chief: Swift Vienna concerts saved from ISIS plot · China eases business visas for Indians

## Also On (14–35) — 22 more stories
Latvia–Russia ties · Le Pen Ukraine scenarios · Iraq–Egypt visit · Trump vs Newsom · Ex-mayor jailed 37mo · Charles–Meghan · Dutch activist euthanasia · Australian retailer collapse · Bangladesh garment workers · Syria–EU displaced persons · Myanmar ICJ Rohingya · Libya Russia-Ukraine proxy · Belarus opposition talks · Kim protection not control · Lavrov Lebanon/Syria · Vietnam trade surplus · Taliban woodlands · US Nvidia-China chips · Russia Kaliningrad ferries · Hanson Queensland trial · Thailand 16km Bangchak march · Anthropic shares fall

## Date Check — deliberately left out
COP31 collapse Antalya (Sun 22 Nov) · Russia 400-drone+110-missile barrage (19–20 Nov) · Kyiv toll 14 killed (22–23 Nov) · Ukraine sinks corvette Merkury (Sun 22 Nov) · Nvidia reinstates Huang (Mon 23 Nov) · Manchester concert evacuation (Sun 22 Nov) · SK education minister quits (Sun 22 Nov) · China sentences official Ma (Mon 23 Nov) · Russian strike near Kyiv presidential complex (Mon 23 Nov) · Houthi attacks Taiz (Mon 23 Nov) · IRGC Hormuz claims (7–20 Nov, unverified)

## Tech
- `tools/generate.py` — pure Python + Pillow, renders `out/entry.png` (1024×1024 RGB, ≤1 MiB)
- `main.ts` — copies committed `out/entry.png` to `MAKEFUN_OUTPUT_DIR` (grader runs this)
- Fonts: DejaVu Serif (headlines), DejaVu Sans (body) — bundled via GitHub release