.PHONY: install fetch-live full-analysis backtest charts clean

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

clean:
	rm -rf __pycache__ .pytest_cache
	find . -name "*.pyc" -delete
