import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

def train_and_save():
    # Create synthetic dataset
    np.random.seed(42)
    n_samples = 500

    # Features: attendance_percentage, avg_assignment_score, past_cgpa
    attendance = np.random.uniform(40, 100, n_samples)
    assignments = np.random.uniform(30, 100, n_samples)
    cgpa = np.random.uniform(4.0, 10.0, n_samples)

    # Label generation logic (dummy)
    # Lower values -> higher chance of failure (1)
    score = (attendance * 0.4) + (assignments * 0.3) + (cgpa * 10 * 0.3)
    # Threshold for failure
    threshold = np.percentile(score, 25) # Bottom 25% at risk
    labels = (score < threshold).astype(int)

    df = pd.DataFrame({
        'attendance': attendance,
        'assignments': assignments,
        'cgpa': cgpa,
        'failure_risk': labels
    })

    X = df[['attendance', 'assignments', 'cgpa']]
    y = df['failure_risk']

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Save the model
    model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_save()
