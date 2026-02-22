import logging
import structlog
import csv
from constants import TRACE_HEADERS, TRACE_FILE

# Configure the logger

# File handler formatter
file_formatter = logging.Formatter('%(message)s')
# Console handler formatter
console_formatter = logging.Formatter('TRACE: %(message)s')
# console_formatter = logging.Formatter('%(levelname)s: %(name)s: %(message)s')

# File handler
file_handler = logging.FileHandler(TRACE_FILE)
file_handler.setLevel(logging.INFO)  # Set the log level for the file
file_handler.setFormatter(file_formatter)
# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the log level for the console
console_handler.setFormatter(console_formatter)
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])


# Define a custom processor to format the log into a CSV row
def csv_processor(logger, method_name, event_dict):
    # Extract values based on the headers defined
    values = [event_dict.get(key, '').__str__() for key in TRACE_HEADERS]
    # return values
    return ','.join(values)


# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
        csv_processor
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Reset the trace file
with open(TRACE_FILE, mode='w', newline='') as file:
    csv_writer = csv.writer(file)
    csv_writer.writerow(TRACE_HEADERS)
