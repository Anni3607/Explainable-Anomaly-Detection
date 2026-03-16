def recommend(event_type):

    if event_type == "CPU_SPIKE":
        return "Optimize CPU-intensive workload or increase instance size."

    if event_type == "MEMORY_SURGE":
        return "Check memory leaks or upgrade RAM allocation."

    if event_type == "RESOURCE_SCALE":
        return "Review autoscaler limits to prevent excessive scaling."

    if event_type == "TRAFFIC_SPIKE":
        return "Use CDN or caching to reduce backend load."

    if event_type == "COST_ANOMALY":
        return "Investigate billing dashboard for abnormal service usage."

    return "No action required"
