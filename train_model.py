import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# === Load your data ===
df = pd.read_csv("calloff_log.csv")

# === Clean it up ===
df = df[df["called_off"].isin(["Yes", "No"])]  # Drop "Not yet"
df.dropna(inplace=True)

# === Encode categorical data ===
le_condition = LabelEncoder()
df["condition_encoded"] = le_condition.fit_transform(df["condition"])

# === Features and target ===
X = df[["score", "flights", "visibility_mi", "condition_encoded"]]
y = (df["called_off"] == "Yes").astype(int)  # 1 = Called off, 0 = Didn't

# === Split data ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Train model ===
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# === Evaluate ===
y_pred = model.predict(X_test)
print("=== Classification Report ===")
print(classification_report(y_test, y_pred))

print("=== Confusion Matrix ===")
print(confusion_matrix(y_test, y_pred))

# === Save the model & encoder ===
joblib.dump(model, "calloff_model.pkl")
joblib.dump(le_condition, "condition_encoder.pkl")

print("✅ Model and encoder saved!")
