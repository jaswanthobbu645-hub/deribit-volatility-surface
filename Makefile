.PHONY: install fetch-live fetch-historical fetch-dvol full-analysis backtest cost-sensitivity reproduce clean test test-verbose

install:
	pip install -r requirements.txt

fetch-live:
	python src/data/fetch_live.py

fetch-historical:
	python src/data/fetch_historical_btc.py
	python src/data/fetch_historical_eth.py

fetch-dvol:
	python src/data/fetch_dvol.py

full-analysis:
	python src/features/full_pipeline.py
	python src/features/compute_metrics.py

backtest:
	python src/strategy/walk_forward.py

cost-sensitivity:
	python src/strategy/cost_sensitivity.py

reproduce: fetch-historical fetch-dvol full-analysis backtest cost-sensitivity
	@echo "Reproduction complete. Check charts/ and data/processed/"

test:
	pytest tests/ -q

test-verbose:
	pytest tests/ -v

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -rf .pytest_cache