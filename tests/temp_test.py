from tradingview_scraper.symbols.ideas import Ideas
# Create an instance of the Ideas class
ideas_scraper = Ideas(
    export_result=True,
    export_type='json'
    )

data = ideas_scraper.scrape(
    symbol="SPY",
    startPage=1,
    endPage=2,
    sort='recent'
    )
with open("reported_ideas_data.json", "w") as f:
    import json
    json.dump(data, f)
