from sklearn.linear_model import LinearRegression
import numpy as np


def forecast_cost(df):

    # Create index for regression
    X = np.arange(len(df)).reshape(-1, 1)

    # Target variable
    y = df["cost"].values

    # Train model
    model = LinearRegression()
    model.fit(X, y)

    # Predict next time step
    future_index = np.array([[len(df)]])

    prediction = model.predict(future_index)

    # prediction is an array like [2.84]
    return float(prediction[0])
