import csv

def get_csv_table(path):
    """
    Gets the CSV object from a file and returns a file handle.
    """
    return csv.reader(open(path))
