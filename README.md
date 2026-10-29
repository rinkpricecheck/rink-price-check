# Rink Price Check

A hockey equipment price comparison site. It lists new, used and pro-stock gear from 17 stores, with filters for category, condition, brand, size and skate size.

- **Site:** `docs/index.html`, published with GitHub Pages.
- **Data:** `scraper/run.py` collects every store's listings and writes `deals.json`, `used-pias.json` (Play It Again Sports) and `status.json`.
- **Schedule:** `.github/workflows/refresh.yml` runs every 8 hours, and also on demand from **Actions → Refresh prices → Run workflow**.

## Store coverage

| Platform | Stores |
|---|---|
| Category pages | Pure Hockey, Pure Goalie, Ice Warehouse |
| Magento | HockeyMonkey, Goalie Monkey, Great Skate |
| Shopify `products.json` | Discount Hockey, Sports Excellence, HockeyTron, HockeyStickMan |
| BigCommerce | Pro Stock Hockey, Play It Again Sports (all listed as Used) |
| Carried over from `seed/` | Stark Hockey, SidelineSwap, Goalies Plus, Sports Etc, xHockeyProducts |

A store might fail or return less than half of its previous item count, for example because it blocks automated requests. When that happens, the site keeps that store's previous listings, so the page never goes empty. Each run's summary (in the Actions tab) shows which stores were refreshed.

For in-stock skate sizes, the scraper opens the skate product pages at Pure Hockey, Pure Goalie, HockeyMonkey, Goalie Monkey, Great Skate and Ice Warehouse. The Shopify stores' product data already includes sizes.

## Run locally

```
pip install -r scraper/requirements.txt
python scraper/run.py build            # previous data comes from seed/
python scraper/run.py build --only "HockeyTron,Discount Hockey"
```
