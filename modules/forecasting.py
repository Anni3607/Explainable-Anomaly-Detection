from sklearn.linear_model import LinearRegression
import numpy as np

def forecast_cost(df):

    df = df.copy()
    df["t"] = np.arange(len(df))

    X = df[["t"]]
    y = df["cost"]

    model = LinearRegression()
    model.fit(X, y)

    next_t = np.array([[len(df)]])

    prediction = model.predict(next_t)

    return float(prediction[0])
