import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

# Load usage data (adjust columns as needed)
data_path = os.path.join('data', 'usage_data.csv')
df = pd.read_csv(data_path)

# Example: Assume last 7 days' usage as features, 8th day as label
# You may need to adjust this logic based on your actual data format
usage = df['usage'].values if 'usage' in df.columns else df.iloc[:, -1].values

X = []
y = []
window = 7
for i in range(len(usage) - window):
    X.append(usage[i:i+window])
    # Label: 0=normal, 1=warning, 2=critical (simple thresholds)
    next_day = usage[i+window]
    if next_day < 5:
        y.append(0)
    elif next_day < 10:
        y.append(1)
    else:
        y.append(2)
X = np.array(X)
y = np.array(y)

# Train model
clf = RandomForestClassifier(n_estimators=50, random_state=42)
clf.fit(X, y)

# Save model
model_path = os.path.join('ml_model', 'model.pkl')
with open(model_path, 'wb') as f:
    pickle.dump(clf, f)

print(f"Model trained and saved to {model_path}")
