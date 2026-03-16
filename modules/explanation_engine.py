def explain(row):

    if row["event_type"] == "CPU_SPIKE":
        return "CPU utilization exceeded safe threshold, increasing compute cost."

    if row["event_type"] == "MEMORY_SURGE":
        return "Abnormal memory consumption detected on the instance."

    if row["event_type"] == "RESOURCE_SCALE":
        return "Autoscaling triggered additional compute resources."

    if row["event_type"] == "TRAFFIC_SPIKE":
        return "Unexpected increase in incoming traffic caused resource scaling."

    if row["event_type"] == "COST_ANOMALY":
        return "Cloud billing deviated significantly from expected baseline."

    return "Routine system activity."
