from sklearn.ensemble import IsolationForest

def detect_anomalies(df):

    model = IsolationForest(
        contamination=0.02,
        random_state=42
    )

    df["anomaly_model"] = model.fit_predict(df[["cost"]])

    df["ml_anomaly"] = df["anomaly_model"] == -1

    return df