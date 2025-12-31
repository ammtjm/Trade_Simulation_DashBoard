from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen
import xml.etree.ElementTree as ET

import pandas as pd
import yfinance as yf


DEFAULT_TICKER = "1802.T"
DEFAULT_NEWS_QUERY = "大林組"


def default_date_range() -> tuple[date, date]:
    end = date.today()
    start = end - timedelta(days=365 * 5)
    return start, end


def fetch_price_history(ticker: str, start: date, end: date) -> pd.DataFrame:
    history = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    if history.empty:
        raise ValueError(f"No price data returned for {ticker}.")
    history = history.reset_index()
    history["Ticker"] = ticker
    return history


def fetch_quarterly_financials(ticker: str) -> dict[str, pd.DataFrame]:
    ticker_data = yf.Ticker(ticker)
    quarterly_financials = {
        "quarterly_income_statement": ticker_data.quarterly_financials,
        "quarterly_balance_sheet": ticker_data.quarterly_balance_sheet,
        "quarterly_cash_flow": ticker_data.quarterly_cashflow,
    }
    return {name: df for name, df in quarterly_financials.items() if not df.empty}


def fetch_news_rss(query: str, limit: int = 20) -> pd.DataFrame:
    if not query:
        raise ValueError("Query must be a non-empty string.")
    if limit <= 0:
        raise ValueError("Limit must be a positive integer.")

    rss_url = (
        "https://news.google.com/rss/search?q="
        f"{quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"
    )
    with urlopen(rss_url) as response:
        rss_content = response.read()

    root = ET.fromstring(rss_content)
    items: list[dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", default="").strip()
        link = item.findtext("link", default="").strip()
        published = item.findtext("pubDate", default="").strip()
        source = ""
        source_element = item.find("source")
        if source_element is not None and source_element.text:
            source = source_element.text.strip()
        items.append(
            {
                "title": title,
                "link": link,
                "published": published,
                "source": source,
            }
        )

    return pd.DataFrame(items)


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Obayashi (1802.T) stock prices and quarterly financials."
    )
    parser.add_argument("--ticker", default=DEFAULT_TICKER, help="Ticker symbol to fetch.")
    parser.add_argument(
        "--start",
        type=lambda value: date.fromisoformat(value),
        default=default_date_range()[0],
        help="Start date (YYYY-MM-DD). Default: 5 years ago.",
    )
    parser.add_argument(
        "--end",
        type=lambda value: date.fromisoformat(value),
        default=default_date_range()[1],
        help="End date (YYYY-MM-DD). Default: today.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "Output",
        help="Directory to store output files.",
    )
    parser.add_argument(
        "--news-query",
        default=DEFAULT_NEWS_QUERY,
        help="Query used for Google News RSS (default: 大林組).",
    )
    parser.add_argument(
        "--news-limit",
        type=int,
        default=20,
        help="Number of news items to fetch (default: 20).",
    )
    return parser.parse_args()


def save_quarterly_financials(
    quarterly_financials: dict[str, pd.DataFrame], output_path: Path
) -> None:
    if not quarterly_financials:
        raise ValueError("Quarterly financials dictionary is empty.")
    with pd.ExcelWriter(output_path) as writer:
        for sheet_name, df in quarterly_financials.items():
            df.to_excel(writer, sheet_name=sheet_name)


def save_news_csv(news: pd.DataFrame, output_path: Path) -> None:
    if news.empty:
        raise ValueError("News DataFrame is empty.")
    news.to_csv(output_path, index=False)


def run(
    *,
    ticker: str = DEFAULT_TICKER,
    start: date | None = None,
    end: date | None = None,
    output_dir: Path | None = None,
    news_query: str = DEFAULT_NEWS_QUERY,
    news_limit: int = 20,
) -> dict[str, Path]:
    start_date, end_date = default_date_range()
    start = start or start_date
    end = end or end_date
    output_dir = output_dir or Path(__file__).resolve().parents[1] / "Output"
    ensure_output_dir(output_dir)

    price_data = fetch_price_history(ticker, start, end)
    price_path = output_dir / f"{ticker}_price_history.csv"
    price_data.to_csv(price_path, index=False)

    quarterly_financials = fetch_quarterly_financials(ticker)
    financials_path = output_dir / f"{ticker}_quarterly_financials.xlsx"
    save_quarterly_financials(quarterly_financials, financials_path)

    news_data = fetch_news_rss(news_query, news_limit)
    news_path = output_dir / f"{ticker}_news.csv"
    save_news_csv(news_data, news_path)

    return {
        "price_history": price_path,
        "quarterly_financials": financials_path,
        "news": news_path,
    }


def main() -> None:
    args = parse_args()
    paths = run(
        ticker=args.ticker,
        start=args.start,
        end=args.end,
        output_dir=args.output_dir,
        news_query=args.news_query,
        news_limit=args.news_limit,
    )

    for label, path in paths.items():
        print(f"Saved {label} to: {path}")


if __name__ == "__main__":
    main()
