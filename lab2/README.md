# Currency Exchange Rate API Client

This Python script interacts with a local currency exchange rate API to fetch exchange rates between different currencies for specified dates. It provides a command-line interface to query exchange rates and automatically saves the results to JSON files.

## Features

- **Command-line interface**: Easy to use with command-line parameters
- **Automatic data saving**: Saves exchange rate data to JSON files with descriptive names
- **Error handling**: Comprehensive error handling with logging to both console and file
- **Date validation**: Validates dates to ensure they're within the supported range (2025-01-01 to 2025-09-15)
- **Currency validation**: Validates currency codes against available currencies from the API
- **Structured output**: Organized file structure with timestamp and request metadata

## Prerequisites

### Dependencies

The script requires Python 3.6+ and the following Python packages:

- `requests` - For making HTTP requests to the API
- `argparse` - For command-line argument parsing (built-in)
- `json` - For JSON data handling (built-in)
- `logging` - For error logging (built-in)
- `datetime` - For date handling (built-in)
- `pathlib` - For file path handling (built-in)

### Installing Dependencies

1. **Install Python 3.6 or higher** (if not already installed):
   ```bash
   # On Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip
   
   # On macOS (using Homebrew)
   brew install python3
   
   # On Windows, download from python.org
   ```

2. **Install the requests library**:
   ```bash
   pip3 install requests
   ```
   
   Or if you prefer using pip:
   ```bash
   pip install requests
   ```

## Usage

### Basic Syntax

```bash
python3 currency_exchange_rate.py <from_currency> <to_currency> <date>
```

### Parameters

- `from_currency`: Source currency code (e.g., USD, EUR, MDL)
- `to_currency`: Target currency code (e.g., USD, EUR, MDL)
- `date`: Date in YYYY-MM-DD format (must be between 2025-01-01 and 2025-09-15)

### Available Currencies

The API supports the following currencies:
- **MDL** - Moldovan Leu (default/base currency)
- **USD** - US Dollar
- **EUR** - Euro
- **RON** - Romanian Leu
- **RUS** - Russian Ruble
- **UAH** - Ukrainian Hryvnia

### Command Examples

1. **Get USD to EUR exchange rate for January 15, 2025**:
   ```bash
   python3 currency_exchange_rate.py USD EUR 2025-01-15
   ```

2. **Get EUR to MDL exchange rate for March 1, 2025**:
   ```bash
   python3 currency_exchange_rate.py EUR MDL 2025-03-01
   ```

3. **Get MDL to USD exchange rate for May 15, 2025**:
   ```bash
   python3 currency_exchange_rate.py MDL USD 2025-05-15
   ```

4. **Get RON to UAH exchange rate for July 1, 2025**:
   ```bash
   python3 currency_exchange_rate.py RON UAH 2025-07-01
   ```

5. **Get UAH to EUR exchange rate for September 10, 2025**:
   ```bash
   python3 currency_exchange_rate.py UAH EUR 2025-09-10
   ```

### Example Output

```
Fetching available currencies...
Available currencies: MDL, USD, EUR, RON, RUS, UAH
Fetching exchange rate from USD to EUR for 2025-01-15...

Exchange Rate Information:
From: USD
To: EUR
Rate: 1.025501172192718
Date: 2025-01-15

Data successfully saved to data/USD_EUR_2025-01-15.json
```

## Script Structure

### Main Components

The script is organized into several key components:

#### 1. CurrencyExchangeClient Class

The main class that handles all API interactions:

- **`__init__()`**: Initializes the client with base URL and API key
- **`setup_logging()`**: Configures logging to both file and console
- **`get_available_currencies()`**: Fetches the list of supported currencies
- **`get_exchange_rate()`**: Fetches exchange rate data for specific currency pair and date
- **`save_data()`**: Saves exchange rate data to JSON files with proper structure

#### 2. Utility Functions

- **`validate_date()`**: Validates date format and ensures it's within the supported range
- **`main()`**: Main function that handles command-line arguments and orchestrates the workflow

#### 3. Error Handling

The script implements comprehensive error handling:

- **Network errors**: Connection timeouts, unreachable host
- **API errors**: Invalid parameters, authentication failures
- **Data errors**: JSON parsing errors, invalid response format
- **Validation errors**: Invalid dates, unsupported currencies
- **File system errors**: Permission issues, disk space problems

### File Organization

The script creates and manages the following file structure:

```
project_root/
├── currency_exchange_rate.py    # Main script
├── error.log                    # Error log file
└── data/                        # Directory for saved exchange rate data
   ├── USD_EUR_2025-01-15.json   # Example data file
   ├── EUR_MDL_2025-03-01.json
   └── ...
```

### Data File Format

Each saved JSON file contains both request metadata and response data:

```json
{
  "request": {
    "from_currency": "USD",
    "to_currency": "EUR", 
    "date": "2025-01-15",
    "timestamp": "2025-09-24T18:55:55.693168"
  },
  "response": {
    "from": "USD",
    "to": "EUR",
    "rate": 1.025501172192718,
    "date": "2025-01-15"
  }
}
```

### Logging System

The script logs important events and errors to:

- **Console**: Real-time feedback for the user
- **error.log file**: Persistent log for debugging and audit purposes

Log entries include timestamps, log levels, and detailed messages.

## Troubleshooting

### Common Issues

1. **"Connection error: Unable to connect to http://localhost:8080"**
   - Ensure the Docker service is running: `docker compose up -d`
   - Check if port 8080 is available: `curl http://localhost:8080`

2. **"requests module not found"**
   - Install the requests library: `pip3 install requests`

3. **"Invalid date" error**
   - Ensure date is in YYYY-MM-DD format
   - Verify date is between 2025-01-01 and 2025-09-15

4. **"Currency 'XXX' is not available"**
   - Check the list of supported currencies: MDL, USD, EUR, RON, RUS, UAH
   - Ensure currency codes are spelled correctly

5. **Permission denied when creating files**
   - Ensure you have write permissions in the current directory
   - Check disk space availability

### Error Log

All errors are logged to `error.log` in the project root. Review this file for detailed error information and troubleshooting.

## Testing

To test the script functionality, run it with various currency pairs and dates:

```bash
# Test with different currency pairs
python3 currency_exchange_rate.py USD EUR 2025-01-15
python3 currency_exchange_rate.py EUR MDL 2025-03-01
python3 currency_exchange_rate.py MDL USD 2025-05-15
python3 currency_exchange_rate.py RON UAH 2025-07-01
python3 currency_exchange_rate.py UAH EUR 2025-09-10

# Test error handling
python3 currency_exchange_rate.py USD EUR 2024-12-31  # Invalid date
python3 currency_exchange_rate.py XXX EUR 2025-01-15  # Invalid currency
```

The script has been tested with multiple date ranges and currency combinations to ensure reliability and proper error handling.