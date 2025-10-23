# Systemd Timer Setup for Auto Cleanup

This directory contains Systemd service and timer configuration files for automatic data cleanup.

## Files

- `estimator-cleanup.service`: Service definition for cleanup batch
- `estimator-cleanup.timer`: Timer definition (runs daily at 2:00 AM)

## Installation

### 1. Copy files to systemd directory

```bash
sudo cp estimator-cleanup.service /etc/systemd/system/
sudo cp estimator-cleanup.timer /etc/systemd/system/
```

### 2. Reload systemd daemon

```bash
sudo systemctl daemon-reload
```

### 3. Enable and start timer

```bash
# Enable timer (auto-start on boot)
sudo systemctl enable estimator-cleanup.timer

# Start timer
sudo systemctl start estimator-cleanup.timer
```

## Verify

### Check timer status

```bash
# Check if timer is active
sudo systemctl status estimator-cleanup.timer

# List all timers
sudo systemctl list-timers --all | grep estimator-cleanup
```

### Check service status

```bash
# Check last execution status
sudo systemctl status estimator-cleanup.service

# View logs
sudo journalctl -u estimator-cleanup.service -n 50
```

## Manual Execution

You can manually run the cleanup batch:

```bash
# Run service once
sudo systemctl start estimator-cleanup.service

# Or run Python script directly
cd /path/to/ai-estimator2/backend
source /path/to/python/bin/activate
conda activate your-python-env
python -m app.tasks.cleanup
```

## Stop/Disable Timer

```bash
# Stop timer
sudo systemctl stop estimator-cleanup.timer

# Disable timer (prevent auto-start)
sudo systemctl disable estimator-cleanup.timer
```

## Configuration

The cleanup batch respects settings in `backend/.env`:

```bash
# Data retention period (days)
DATA_RETENTION_DAYS=30

# Enable/disable auto cleanup
AUTO_CLEANUP_ENABLED=true
```

## Troubleshooting

### Timer not running

```bash
# Check timer list
sudo systemctl list-timers --all

# Check timer status
sudo systemctl status estimator-cleanup.timer

# Check service logs
sudo journalctl -u estimator-cleanup.service -n 100
```

### Permission errors

Make sure the service runs as `your-username` and has access to:
- `/path/to/ai-estimator2/backend/`
- SQLite database file (`app.db`)
- Upload/result file directories

## Notes

- Timer runs daily at 2:00 AM (JST)
- If the system is off at the scheduled time, the timer will run 5 minutes after boot (`Persistent=true`)
- Cleanup deletes tasks older than `DATA_RETENTION_DAYS` (default: 30 days)
- All related data (deliverables, Q&A pairs, estimates, messages, files) are deleted together
