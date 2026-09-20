import os
import glob
import pandas as pd
import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
PROCESSED = os.path.join(ROOT, 'data', 'processed')
CHARTS = os.path.join(ROOT, 'charts')


class TestFilesExist:
    def test_btc_surface(self):
        assert os.path.exists(os.path.join(PROCESSED, 'BTC_surface_1y.csv'))
    
    def test_eth_surface(self):
        assert os.path.exists(os.path.join(PROCESSED, 'ETH_surface_1y.csv'))
    
    def test_dvol_btc(self):
        assert os.path.exists(os.path.join(PROCESSED, 'dvol_BTC_1y.csv'))
    
    def test_charts(self):
        expected = ['event_study_final.png', 'term_structure_butterfly.png',
                    'surface_3d.png', 'crypto_vs_equity.png', 'eth_fed_study.png']
        for c in expected:
            assert os.path.exists(os.path.join(CHARTS, c))


class TestDataIntegrity:
    def test_btc_surface_has_data(self):
        df = pd.read_csv(os.path.join(PROCESSED, 'BTC_surface_1y.csv'))
        assert len(df) > 1000
        assert 'strike' in df.columns
        assert 'implied_volatility' in df.columns
    
    def test_iv_reasonable(self):
        df = pd.read_csv(os.path.join(PROCESSED, 'BTC_surface_1y.csv'))
        iv = df['implied_volatility'].dropna()
        # Some IVs are garbage from scraper (Newton-Raphson non-convergence).
        # Verify >95% of IVs are in [0, 3]. Acknowledge noise honestly.
        reasonable = iv[(iv >= 0) & (iv <= 3.0)]
        pct_reasonable = len(reasonable) / len(iv)
        assert pct_reasonable > 0.95, f"Only {pct_reasonable*100:.1f}% of IVs are in [0, 3]"
        assert iv.min() >= 0


class TestNoJunk:
    def test_no_orig_files(self):
        assert len(glob.glob('**/*.orig', recursive=True)) == 0
    
    def test_no_rej_files(self):
        assert len(glob.glob('**/*.rej', recursive=True)) == 0
    
    def test_no_conflict_markers(self):
        for f in glob.glob('src/**/*.py', recursive=True):
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
            assert '<<<<<<<' not in content
