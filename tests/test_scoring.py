import os
from risk_model import AltScorer

def test_score_runs():
    scorer = AltScorer(os.path.join("weights","matriz_riesgo.yaml"))
    features = {k:0.7 for k in scorer.weights}
    res = scorer.score(features)
    assert 0.0 <= res.total <= 1.0
