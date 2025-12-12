"""
Advanced Ballistics AI & ML Analysis

This module provides:
- MOA/ES/SD prediction (Gradient Boosting)
- Pressure prediction (Neural Network)
- Barrel life forecasting (Prophet)
- Computer vision group measurement (OpenCV)
- Feature importance (SHAP)
- Multi-objective optimization (Genetic Algorithm)
"""

from src.utils.optional_deps import cv2, HAS_CV2
import numpy as np

# Optional heavy ML/CV dependencies - import guarded so module can be imported
# in minimal environments. Functions that require these libs should check
# the corresponding variable and raise a clear ImportError if used.
shap = None
tf = None
Prophet = None
GradientBoostingRegressor = None


# 1. MOA/ES/SD Prediction (Gradient Boosting)
def train_accuracy_predictor(X, y):
    global GradientBoostingRegressor
    if GradientBoostingRegressor is None:
        try:
            from sklearn.ensemble import GradientBoostingRegressor as _GBR

            GradientBoostingRegressor = _GBR
        except Exception:
            raise ImportError(
                "scikit-learn GradientBoostingRegressor is required for train_accuracy_predictor"
            )

    model = GradientBoostingRegressor(
        n_estimators=1000, learning_rate=0.01, max_depth=8, min_samples_split=5
    )
    model.fit(X, y)
    return model


def predict_accuracy(model, X_new):
    return model.predict(X_new)


# 2. Pressure Prediction (Neural Network)
def train_pressure_nn(X, y):
    global tf
    if tf is None:
        try:
            import tensorflow as _tf

            tf = _tf
        except Exception:
            raise ImportError("TensorFlow is required for train_pressure_nn")

    model = tf.keras.Sequential(
        [
            tf.keras.layers.Dense(128, activation="relu", input_shape=(X.shape[1],)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=100, validation_split=0.2)
    return model


def predict_pressure(model, X_new):
    return model.predict(X_new)


# 3. Barrel Life Forecasting (Prophet)
def forecast_barrel_life(df):
    # df: columns ['ds' (date), 'rounds_fired', 'y' (MOA)]
    global Prophet
    if Prophet is None:
        try:
            from prophet import Prophet as _Prophet

            Prophet = _Prophet
        except Exception:
            raise ImportError("Prophet is required for forecast_barrel_life")

    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=10)
    forecast = model.predict(future)
    return forecast


# 4. Computer Vision Group Measurement (OpenCV)
def measure_group_size(image_path):
    if not HAS_CV2 or cv2 is None:
        raise ImportError("OpenCV (cv2) is required for measure_group_size but is not installed.")

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) < 2:
        return None
    centers = [cv2.moments(cnt) for cnt in contours]
    centers = [
        (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))
        for m in centers
        if m["m00"] != 0
    ]
    dists = [
        np.linalg.norm(np.array(centers[i]) - np.array(centers[j]))
        for i in range(len(centers))
        for j in range(i + 1, len(centers))
    ]
    max_dist = max(dists) if dists else None
    return max_dist


# 5. Feature Importance (SHAP)
def explain_model(model, X):
    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)
    shap.summary_plot(shap_values, X)
    return shap_values


# 6. Multi-Objective Optimization (Genetic Algorithm)
# Placeholder: Use NSGA2 or similar library for real implementation
# ...existing code...
