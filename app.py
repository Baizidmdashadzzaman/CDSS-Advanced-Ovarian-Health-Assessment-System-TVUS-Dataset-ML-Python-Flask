from flask import Flask, render_template, request
import joblib
import json
import pandas as pd
import numpy as np

app = Flask(__name__)


model = joblib.load('model_assets/ovarian_model.pkl')
with open('model_assets/model_metadata.json', 'r') as f:
    metadata = json.load(f)

FEATURES = metadata['selected_features']


def get_clinical_guidelines(prob):
    if prob < 0.30:
        tier = "Low Risk"
        color = "#1e3a8a"  
        rec = "Routine follow-up in 6–12 months recommended. Standard TVUS screening."
    elif 0.30 <= prob < 0.70:
        tier = "Moderate Risk"
        color = "#f59e0b"  
        rec = "Consider CA-125 blood test and repeat TVUS in 3 months for monitoring."
    else:
        tier = "High Risk"
        color = "#ef4444"  
        rec = "Urgent referral to Gynecologic Oncologist. Immediate biopsy or surgical consultation recommended."
    return tier, color, rec


@app.route('/')
def home():
    return render_template('index.html', features=FEATURES)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data_dict = {f: [float(request.form.get(f, 0))] for f in FEATURES}
        input_df = pd.DataFrame(data_dict)[FEATURES]

        prob = model.predict_proba(input_df)[0][1]
        risk_tier, risk_color, recommendation = get_clinical_guidelines(prob)

        importances = model.calibrated_classifiers_[0].estimator.feature_importances_
        feature_impact = []
        for i, feat in enumerate(FEATURES):
            impact = float(importances[i] * 100)
            feature_impact.append({"feature": feat.replace('_', ' ').title(), "impact": round(impact, 2)})

        feature_impact = sorted(feature_impact, key=lambda x: x['impact'], reverse=True)[:6]

        return render_template('index.html',
                               features=FEATURES,
                               prob=round(prob * 100, 2),
                               risk_tier=risk_tier,
                               risk_color=risk_color,
                               recommendation=recommendation,
                               feature_impact=json.dumps(feature_impact),
                               show_results=True)
    except Exception as e:
        return render_template('index.html', features=FEATURES, error=str(e))


if __name__ == '__main__':
    app.run(debug=True)