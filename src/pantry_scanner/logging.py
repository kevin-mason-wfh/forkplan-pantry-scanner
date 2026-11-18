from aws_lambda_powertools import Logger, Metrics

logger = Logger(service="pantry-scanner")
metrics = Metrics(namespace="Forkplan/PantryScanner", service="pantry-scanner")
