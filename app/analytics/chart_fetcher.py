# app/analytics/chart_fetcher.py

import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from markupsafe import Markup
import requests
from dotenv import load_dotenv

load_dotenv("alpaca_keys.env")
load_dotenv("alphavantage.env")

ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

def get_chart_html(symbol='AAPL', interval_label='1DAY', mode='mock',
                   show_volume=True, chart_type='candlestick',
                   intel_layer=False, pulse_dot=True, study_rsi=False):
    symbol = symbol.upper()
    interval_label = interval_label.upper()

    try:
        if mode == 'mock':
            path = f"mock_engine_cache/{symbol}_{interval_label}.csv"
            if not os.path.exists(path):
                raise FileNotFoundError(f"Mock data not found: {path}")
            df = pd.read_csv(path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        elif mode == 'realtime':
            function_map = {
                "1DAY": ("TIME_SERIES_INTRADAY", "60min"),
                "5DAY": ("TIME_SERIES_INTRADAY", "30min"),
                "15DAY": ("TIME_SERIES_INTRADAY", "60min"),
                "30DAY": ("TIME_SERIES_DAILY", None),
                "90DAY": ("TIME_SERIES_DAILY", None),
                "180DAY": ("TIME_SERIES_DAILY", None),
                "360DAY": ("TIME_SERIES_DAILY", None),
                "YTD": ("TIME_SERIES_DAILY", None),
                "MAX": ("TIME_SERIES_MONTHLY", None)
            }
            function, interval = function_map.get(interval_label, ("TIME_SERIES_DAILY", None))
            url = "https://www.alphavantage.co/query"
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": ALPHAVANTAGE_API_KEY,
                "outputsize": "full"
            }
            if interval:
                params["interval"] = interval

            response = requests.get(url, params=params)
            data = response.json()

            if "Note" in data:
                raise ValueError("Alpha Vantage API limit hit.")
            if "Error Message" in data:
                raise ValueError("Invalid request or symbol.")

            ts_key = next((k for k in data if "Time Series" in k), None)
            if not ts_key:
                raise ValueError("Time series data not found.")

            df = pd.DataFrame.from_dict(data[ts_key], orient='index')
            df.columns = [c.split(". ")[-1].capitalize() for c in df.columns]
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
            df.index = pd.to_datetime(df.index, errors='coerce')
            df = df[~df.index.duplicated(keep='last')]
            df.sort_index(inplace=True)
            if chart_type == 'line' and len(df) > 300:
                df = df.iloc[-300:]
            df['timestamp'] = df.index

        else:
            raise ValueError("Unknown mode.")

        df.set_index('timestamp', inplace=True)

        latest = df.iloc[-1]
        fig = make_subplots(
            rows=3 if study_rsi else 2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.6, 0.25, 0.15] if study_rsi else [0.7, 0.3],
            specs=[[{"type": "xy"}], [{"type": "bar"}]] + ([[{"type": "scatter"}]] if study_rsi else [])
        )

        # ── Main Price Plot ──
        if chart_type == 'line':
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                line=dict(color="#81D8D0"),
                name="Price Line",
                connectgaps=True
            ), row=1, col=1)
            if pulse_dot:
                fig.add_trace(go.Scatter(
                    x=[df.index[-1]],
                    y=[df["Close"].iloc[-1]],
                    mode="markers",
                    marker=dict(size=10, color='#81D8D0'),
                    showlegend=False,
                    name="Last Price Dot"
                ), row=1, col=1)
        else:
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                increasing_line_color="#81D8D0",
                decreasing_line_color="#FF6347",
                name="Price"
            ), row=1, col=1)

        # ── Volume Bars ──
        if show_volume and "Volume" in df.columns:
            volume_colors = np.where(df["Close"] > df["Open"], "limegreen",
                                     np.where(df["Close"] < df["Open"], "tomato", "gray"))
            fig.add_trace(go.Bar(
                x=df.index,
                y=df["Volume"],
                marker_color=volume_colors,
                name="Volume",
                opacity=0.7
            ), row=2, col=1)

        # ── RSI ──
        if study_rsi:
            delta = df["Close"].diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = -delta.clip(upper=0).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            fig.add_trace(go.Scatter(
                x=df.index,
                y=rsi,
                mode="lines",
                line=dict(color="violet", width=1.5),
                name="RSI (14)"
            ), row=3, col=1)
            fig.update_yaxes(title="RSI", row=3, col=1, color='white', side='right')

        # ── INTEL Support/Resistance ──
        if intel_layer:
            try:
                recent_high = df["High"].rolling(window=20).max().iloc[-1]
                recent_low = df["Low"].rolling(window=20).min().iloc[-1]

                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=[recent_high]*len(df),
                    mode="lines",
                    name="Resistance",
                    line=dict(color="red", dash="dash")
                ), row=1, col=1)

                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=[recent_low]*len(df),
                    mode="lines",
                    name="Support",
                    line=dict(color="green", dash="dash")
                ), row=1, col=1)

            except Exception as e:
                print(f"Intel Layer Error: {e}")

        # ── Layout ──
        fig.update_layout(
            title=f"{symbol} - {interval_label} ({mode})",
            template='plotly_dark',
            height=850 if study_rsi else 750,
            plot_bgcolor="#000",
            paper_bgcolor="#000",
            margin=dict(l=40, r=40, t=60, b=40),
            dragmode=False,
            hovermode='x unified',
            xaxis=dict(
                showgrid=False,
                color='white',
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikecolor="#81D8D0",
                spikethickness=1
            ),
            xaxis_rangeslider=dict(visible=False),  # 🔧 Hide zoom pane
            yaxis=dict(
                showgrid=False,
                color='white',
                title='Price',
                side='right',
                showspikes=True,
                spikemode="across",
                spikesnap="cursor",
                spikecolor="#81D8D0",
                spikethickness=1
            ),
            yaxis2=dict(
                showgrid=False,
                color='white',
                title='Volume',
                side='right'
            ),
            annotations=[{
                'text': (
                    f"<b>{symbol}</b><br>"
                    f"Open: {latest['Open']}<br>"
                    f"High: {latest['High']}<br>"
                    f"Low: {latest['Low']}<br>"
                    f"Close: {latest['Close']}<br>"
                    f"Volume: {int(latest['Volume'])}"
                ),
                'align': 'left',
                'showarrow': False,
                'x': 0.01,
                'y': 0.97,
                'xref': 'paper',
                'yref': 'paper',
                'bgcolor': '#111',
                'bordercolor': '#81D8D0',
                'borderwidth': 1,
                'font': dict(size=12, color='white'),
            }]
        )

        return Markup(fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
            config={
                'scrollZoom': True,
                'displayModeBar': True,
                'responsive': True,
                'modeBarButtonsToRemove': ["zoom2d", "zoomIn2d", "zoomOut2d", "resetScale2d"]
            }
        ))

    except Exception as e:
        return Markup(f"<h3 style='color:red;'>Chart Error: {e}</h3>")
