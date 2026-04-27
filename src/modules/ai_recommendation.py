import numpy as np
from sklearn.ensemble import RandomForestRegressor


class AIRecommendationEngine:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)

    def train(self, X, y):
        """
        Train the AI model with input features and target values.

        :param X: Feature matrix (e.g., powder charge, bullet weight).
        :param y: Target values (e.g., group size, velocity).
        """
        self.model.fit(X, y)

    def recommend(self, X_new):
        """
        Generate recommendations based on the trained model.

        :param X_new: New input features for prediction.
        :return: Predicted values.
        """
        return self.model.predict(X_new)


if __name__ == "__main__":
    # Example usage
    engine = AIRecommendationEngine()

    # Example training data
    X_train = np.array(
        [
            [40.0, 140.0],  # [powder charge, bullet weight]
            [42.0, 150.0],
            [44.0, 160.0],
        ]
    )
    y_train = np.array([0.5, 0.4, 0.6])  # Group size in MOA

    engine.train(X_train, y_train)

    # Example prediction
    X_new = np.array([[41.0, 145.0]])
    recommendation = engine.recommend(X_new)
    print("Recommended group size (MOA):", recommendation)
