# Data directory
This directory contains:
- SQLite database (`spy_leaps.db`)
- Downloaded CSV files
- Exported reports

## Database Schema

### Tables:
- `prices`: Daily SPY price history (OHLCV)
- `vix`: Daily VIX data
- `trades`: Backtest trade records
- `signals`: Trading signals (BUY, PAUSE, LIQUIDATE, RESUME)
- `config`: Strategy configuration snapshots

## Backup

To backup your data:
```bash
cp data/spy_leaps.db data/spy_leaps_backup_$(date +%Y%m%d).db
```
