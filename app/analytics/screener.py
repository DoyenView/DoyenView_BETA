def get_top_movers():
    # Temporary Mock Data (until we connect real APIs)
    movers = {
        "Top Gainers": [
            {"Ticker": "AAPL", "Change": "+3.4%"},
            {"Ticker": "NVDA", "Change": "+5.2%"},
            {"Ticker": "TSLA", "Change": "+2.7%"}
        ],
        "Top Losers": [
            {"Ticker": "INTC", "Change": "-2.1%"},
            {"Ticker": "F", "Change": "-1.8%"},
            {"Ticker": "GM", "Change": "-1.5%"}
        ]
    }
    return movers

