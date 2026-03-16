from sklearn.linear_model import LinearRegression
import numpy as np

def forecast_cost(df):

    X = np.arange(len(df)).reshape(-1,1)
    y = df["cost"].values

    model = LinearRegression()
    model.fit(X, y)

    future_index = np.array([[len(df) + 1]])

    prediction = model.predict(future_index)

    return float(prediction)
