import joblib
import numpy as np
import pandas as pd
import shap
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

FEATURE_NAMES = [
    'school', 'sex', 'age', 'address', 'famsize', 'Pstatus',
    'Medu', 'Fedu', 'Mjob', 'Fjob', 'reason', 'guardian',
    'traveltime', 'studytime', 'failures', 'schoolsup', 'famsup',
    'paid', 'activities', 'nursery', 'higher', 'internet', 'romantic',
    'famrel', 'freetime', 'goout', 'Dalc', 'Walc', 'health',
    'absences', 'G1', 'G2', 'G3'
]

# Categorical encoding maps
CAT_MAP = {
    'school':     {'GP': 0, 'MS': 1},
    'sex':        {'F': 0, 'M': 1},
    'address':    {'R': 0, 'U': 1},
    'famsize':    {'GT3': 0, 'LE3': 1},
    'Pstatus':    {'A': 0, 'T': 1},
    'Mjob':       {'at_home': 0, 'health': 1, 'other': 2, 'services': 3, 'teacher': 4},
    'Fjob':       {'at_home': 0, 'health': 1, 'other': 2, 'services': 3, 'teacher': 4},
    'reason':     {'course': 0, 'home': 1, 'other': 2, 'reputation': 3},
    'guardian':   {'father': 0, 'mother': 1, 'other': 2},
    'schoolsup':  {'no': 0, 'yes': 1},
    'famsup':     {'no': 0, 'yes': 1},
    'paid':       {'no': 0, 'yes': 1},
    'activities': {'no': 0, 'yes': 1},
    'nursery':    {'no': 0, 'yes': 1},
    'higher':     {'no': 0, 'yes': 1},
    'internet':   {'no': 0, 'yes': 1},
    'romantic':   {'no': 0, 'yes': 1},
}

class MLModel:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.explainer = shap.TreeExplainer(self.model)
        print("Model and explainer loaded successfully.")

    def encode_input(self, data: dict) -> np.ndarray:
        """Encode a dict of raw student features into model input array."""
        row = []
        for feat in FEATURE_NAMES:
            val = data.get(feat, 0)
            if feat in CAT_MAP:
                val = CAT_MAP[feat].get(str(val), 0)
            row.append(float(val))
        return np.array(row).reshape(1, -1)

    def predict_risk(self, data: dict) -> dict:
        X = self.encode_input(data)
        risk_score = float(self.model.predict_proba(X)[0][1]) * 100

        if risk_score >= 60:
            risk_label = "High"
        elif risk_score >= 35:
            risk_label = "Medium"
        else:
            risk_label = "Low"

        # SHAP explanation
        shap_values = self.explainer(X)
        vals = shap_values.values[0]
        if hasattr(vals, 'flatten'):
            vals = vals.flatten()
        shap_dict = {
            feat: round(float(v), 4)
            for feat, v in zip(FEATURE_NAMES, vals)
        }

        # Top 3 risk factors
        top_factors = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        explanation = "Top risk factors: " + ", ".join([f[0] for f in top_factors])

        return {
            "risk_score": round(risk_score, 2),
            "risk_label": risk_label,
            "shap_values": shap_dict,
            "explanation": explanation
        }

prediction_service = MLModel()
