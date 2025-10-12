# Lab 03: Task Scheduler (cron) Configuration

This project automates the collection of currency exchange rates using cron jobs running inside a Docker container. The system periodically fetches MDL (Moldovan Leu) exchange rates and stores them in JSON files.

## Project Structure

```
lab03/
├── Dockerfile                 # Docker image configuration
├── docker-compose.yml         # Docker Compose configuration
├── entrypoint.sh              # Container startup script
├── cronjob                    # Cron job definitions
├── currency_exchange_rate.py  # Python script for fetching exchange rates
├── readme.md                  # This file
├── data/                      # Directory for storing exchange rate data (created at runtime)
└── logs/                      # Directory for cron logs (created at runtime)
```

## File Descriptions

### `currency_exchange_rate.py`
Python script that fetches currency exchange rates from an API and saves them to JSON files. It requires three arguments:
- Source currency (e.g., MDL)
- Target currency (e.g., EUR, USD)
- Date in YYYY-MM-DD format

### `cronjob`
Defines two scheduled tasks:
1. **Daily at 6:00 AM**: Fetches MDL to EUR exchange rate for the previous day
2. **Weekly on Friday at 5:00 PM**: Fetches MDL to USD exchange rate for the previous week

### `entrypoint.sh`
Shell script that:
- Creates the log file `/var/log/cron.log`
- Starts monitoring the log file in the background
- Launches the cron daemon in foreground mode

### `Dockerfile`
Builds a Docker image that:
- Uses Python 3.11 as the base image
- Installs cron and Python dependencies (requests library)
- Copies the script, cronjob, and entrypoint files
- Configures cron to execute scheduled tasks
- Sets up logging to `/var/log/cron.log`

### `docker-compose.yml`
Orchestrates the container deployment:
- Builds the image from the Dockerfile
- Mounts volumes for persistent data and logs
- Sets the timezone to Europe/Chisinau
- Configures restart policy

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 1.29 or higher)
- Currency exchange rate API service (see notes below)

## Building and Running the Container

### 1. Build the Docker Image

Navigate to the lab03 directory and build the image:

```bash
cd lab03
docker compose build
```

### 2. Start the Container

Run the container in detached mode:

```bash
docker compose up -d
```

The container will start and begin running cron jobs according to the schedule defined in the `cronjob` file.

### 3. Stop the Container

To stop the running container:

```bash
docker compose down
```

## Verifying Cron Execution

### Check Container Status

Verify the container is running:

```bash
docker compose ps
```

### View Real-time Logs

Monitor the cron logs in real-time:

```bash
docker compose logs -f currency-cron
```

Or directly view the cron log file:

```bash
docker exec currency-exchange-cron tail -f /var/log/cron.log
```

### Check Cron Jobs are Installed

Verify that cron jobs are properly configured:

```bash
docker exec currency-exchange-cron crontab -l
```

### View Saved Exchange Rate Data

The exchange rate data is saved in the `data/` directory:

```bash
ls -la data/
cat data/MDL_EUR_*.json
```

### Access Container Shell

To manually inspect the container:

```bash
docker exec -it currency-exchange-cron /bin/sh
```

Inside the container, you can:
- Check cron status: `ps aux | grep cron`
- View log file: `cat /var/log/cron.log`
- List data files: `ls -la /app/data/`

## Testing the Script Manually

You can test the currency exchange script manually inside the container:

```bash
docker exec currency-exchange-cron python3 /app/currency_exchange_rate.py MDL EUR 2025-10-11
```

## Important Notes

### API Service Dependency

The `currency_exchange_rate.py` script requires a currency exchange API service to be running. By default, it connects to `http://localhost:8080`. 

**To use this project:**

1. Ensure the API service from lab02prep is running
2. Update the script or environment variables to point to the correct API endpoint
3. You may need to configure Docker networking to allow the container to access the API service

### Timezone Configuration

The container is configured to use `Europe/Chisinau` timezone. This ensures cron jobs run at the correct local time. You can modify this in `docker-compose.yml` if needed.

### Date Calculations

The cron jobs use shell date commands to calculate:
- `$(date -d "yesterday" +%Y-%m-%d)` - Gets yesterday's date
- `$(date -d "last friday" +%Y-%m-%d)` - Gets the date of last Friday

### Log Management

All cron output (stdout and stderr) is redirected to `/var/log/cron.log`. The log file is accessible from the host machine via the mounted volume at `./logs/cron.log`.

### Data Persistence

Exchange rate data is stored in the `./data/` directory on the host machine through a Docker volume mount. This ensures data persists even if the container is removed.

## Troubleshooting

### Cron Jobs Not Running

1. Check if cron daemon is running:
   ```bash
   docker exec currency-exchange-cron ps aux | grep cron
   ```

2. Verify cron jobs are loaded:
   ```bash
   docker exec currency-exchange-cron crontab -l
   ```

3. Check for errors in the log:
   ```bash
   docker exec currency-exchange-cron cat /var/log/cron.log
   ```

### API Connection Issues

If the script cannot connect to the API:
1. Verify the API service is running
2. Check network connectivity between containers
3. Review error logs: `docker compose logs currency-cron`

### Permission Issues

If you encounter permission errors:
1. Ensure `entrypoint.sh` has execute permissions
2. Verify log file permissions: `chmod 666 /var/log/cron.log`

## Manual Testing Schedule

Since cron jobs run at specific times, you may want to test them manually:

```bash
# Test daily job (MDL to EUR for yesterday)
docker exec currency-exchange-cron /bin/sh -c "cd /app && python3 currency_exchange_rate.py MDL EUR \$(date -d 'yesterday' +%Y-%m-%d)"

# Test weekly job (MDL to USD for last Friday)
docker exec currency-exchange-cron /bin/sh -c "cd /app && python3 currency_exchange_rate.py MDL USD \$(date -d 'last friday' +%Y-%m-%d)"
```
