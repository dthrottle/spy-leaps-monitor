#!/bin/bash

# SPY LEAPS Monitor - Run Script
# This script helps you run the application in different modes

show_help() {
    echo "SPY LEAPS Monitor - Run Script"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start         Quick start - download data and launch app"
    echo "  app           Launch Streamlit app only"
    echo "  download      Download SPY and VIX data"
    echo "  test          Run test suite"
    echo "  test-cov      Run tests with coverage report"
    echo "  clean         Clean database and temp files"
    echo "  install       Install dependencies"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh start       # First time setup"
    echo "  ./run.sh app         # Launch app if data already exists"
    echo "  ./run.sh test        # Run tests"
    echo ""
}

case "$1" in
    start)
        echo "Starting SPY LEAPS Monitor..."
        if [ -d "venv" ]; then
            venv/bin/python start.py
        else
            python3 start.py
        fi
        ;;
    
    app)
        echo "Launching Streamlit app..."
        if [ -d "venv" ]; then
            venv/bin/streamlit run src/main.py
        else
            streamlit run src/main.py
        fi
        ;;
    
    download)
        echo "Downloading market data..."
        if [ -d "venv" ]; then
            venv/bin/python src/download_data.py --ticker SPY --table prices --start 2010-01-01
            venv/bin/python src/download_data.py --ticker ^VIX --table vix --start 2010-01-01
        else
            python3 src/download_data.py --ticker SPY --table prices --start 2010-01-01
            python3 src/download_data.py --ticker ^VIX --table vix --start 2010-01-01
        fi
        ;;
    
    test)
        echo "Running tests..."
        if [ -d "venv" ]; then
            venv/bin/pytest tests/ -v
        else
            pytest tests/ -v
        fi
        ;;
    
    test-cov)
        echo "Running tests with coverage..."
        if [ -d "venv" ]; then
            venv/bin/pytest tests/ --cov=src --cov-report=html --cov-report=term
        else
            pytest tests/ --cov=src --cov-report=html --cov-report=term
        fi
        echo ""
        echo "Coverage report saved to htmlcov/index.html"
        ;;
    
    clean)
        echo "Cleaning database and temp files..."
        rm -f data/*.db
        rm -f data/*.db-journal
        rm -rf __pycache__
        rm -rf src/__pycache__
        rm -rf tests/__pycache__
        rm -rf .pytest_cache
        rm -rf htmlcov
        rm -rf .coverage
        echo "Done!"
        ;;
    
    install)
        echo "Installing dependencies..."
        pip3 install -r requirements.txt
        echo "Done!"
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
