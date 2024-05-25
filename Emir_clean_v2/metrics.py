
def calc_AHI(apnea_count, hypopnea_count, total_sleep_time):
    """_summary_
    Calculate the Apnea-Hypopnea Index (AHI) using the formula:
    AHI = (Apnea count + Hypopnea count) / Total sleep time

    Args:
    apnea_count (int): The total number of apneas during the study.
    hypopnea_count (int): The total number of hypopneas during the study.
    total_sleep_time (float): The total amount of sleep time during the study.

    Returns:
    float: The Apnea-Hypopnea Index (AHI) calculated using the formula.
    """
    return (apnea_count + hypopnea_count) / total_sleep_time