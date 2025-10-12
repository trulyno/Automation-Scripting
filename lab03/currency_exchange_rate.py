#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

class CurrencyExchangeClient:

    def __init__(self, base_url: str = "http://localhost:8080", api_key: str = "EXAMPLE_API_KEY"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
        self.setup_logging()
    
    def setup_logging(self):
        # Create logs directory if it doesn't exist
        log_file = Path("error.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_available_currencies(self):
        try:
            response = self.session.post(
                f"{self.base_url}/?currencies",
                data={"key": self.api_key}
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("error"):
                self.logger.error(f"API error getting currencies: {data['error']}")
                return None
            
            return data.get("data", [])
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error getting currencies: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error getting currencies: {e}")
            return None
    
    def get_exchange_rate(self, from_currency, to_currency, date = None):
        try:
            params = {
                "from": from_currency.upper(),
                "to": to_currency.upper()
            }
            
            if date:
                params["date"] = date
            
            response = self.session.post(
                self.base_url,
                params=params,
                data={"key": self.api_key}
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("error"):
                self.logger.error(f"API error: {data['error']}")
                return None
            
            return data.get("data")
        
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: Unable to connect to {self.base_url}. Make sure the API service is running.")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            return None

    def save_data(self, data, from_currency, to_currency, date):
        try:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            filename = f"{from_currency.upper()}_{to_currency.upper()}_{date}.json"
            filepath = data_dir / filename
            
            save_data = {
                "request": {
                    "from_currency": from_currency.upper(),
                    "to_currency": to_currency.upper(),
                    "date": date,
                    "timestamp": datetime.now().isoformat()
                },
                "response": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data saved to {filepath}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            return False


def validate_date(date_string):
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 9, 15)
        
        return start_date <= date_obj <= end_date
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Get currency exchange rates from the API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
                python currency_exchange_rate.py USD EUR 2025-03-15
                python currency_exchange_rate.py MDL USD 2025-06-01
                python currency_exchange_rate.py EUR RON 2025-01-01
            """
    )
    
    parser.add_argument("from_currency", help="Source currency code (e.g., USD, EUR)")
    parser.add_argument("to_currency", help="Target currency code (e.g., USD, EUR)")
    parser.add_argument("date", help="Date in YYYY-MM-DD format (2025-01-01 to 2025-09-15)")
    
    args = parser.parse_args()
    
    if not validate_date(args.date):
        print(f"Error: Invalid date '{args.date}'. Date must be in YYYY-MM-DD format and between 2025-01-01 and 2025-09-15.")
        sys.exit(1)
    
    client = CurrencyExchangeClient()
    
    print("Fetching available currencies...")
    currencies = client.get_available_currencies()
    if currencies is None:
        print("Error: Could not fetch available currencies. Check if the API service is running.")
        sys.exit(1)
    
    print(f"Available currencies: {', '.join(currencies)}")
    
    from_currency = args.from_currency.upper()
    to_currency = args.to_currency.upper()
    
    if from_currency not in currencies:
        print(f"Error: Currency '{from_currency}' is not available.")
        sys.exit(1)
    
    if to_currency not in currencies:
        print(f"Error: Currency '{to_currency}' is not available.")
        sys.exit(1)
    
    print(f"Fetching exchange rate from {from_currency} to {to_currency} for {args.date}...")
    exchange_data = client.get_exchange_rate(from_currency, to_currency, args.date)
    
    if exchange_data is None:
        print("Error: Could not fetch exchange rate data.")
        sys.exit(1)
    
    print(f"\nExchange Rate Information:")
    print(f"From: {exchange_data['from']}")
    print(f"To: {exchange_data['to']}")
    print(f"Rate: {exchange_data['rate']}")
    print(f"Date: {exchange_data['date']}")
    
    if client.save_data(exchange_data, from_currency, to_currency, args.date):
        print(f"\nData successfully saved to data/{from_currency}_{to_currency}_{args.date}.json")
    else:
        print("Error: Failed to save data.")
        sys.exit(1)


if __name__ == "__main__":
    main()