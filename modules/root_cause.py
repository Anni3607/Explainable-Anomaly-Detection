def cost_drivers(df):

    drivers = df.groupby("event_type")["cost"].mean().sort_values(ascending=False)

    return drivers