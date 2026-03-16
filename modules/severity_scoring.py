def severity(z):

    if abs(z) > 4:
        return "CRITICAL"

    if abs(z) > 3:
        return "HIGH"

    if abs(z) > 2:
        return "MEDIUM"

    return "LOW"
