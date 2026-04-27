from scipy.stats import norm


def bayesian_analysis(data):
    """
    Perform Bayesian analysis on the given data.

    :param data: List of data points.
    :return: Dictionary with Bayesian analysis results.
    """
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance**0.5

    # Example: Assuming a normal prior
    prior = norm(loc=mean, scale=std_dev)
    posterior = {"mean": prior.mean(), "std_dev": prior.std()}
    return posterior


# Example usage
if __name__ == "__main__":
    sample_data = [850, 860, 845, 870, 855]
    results = bayesian_analysis(sample_data)
    print("Bayesian Analysis Results:", results)
