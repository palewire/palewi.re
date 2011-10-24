import os
import csv
from dateutil.parser import parse
from models import FreeFluVaccine
from googlegeocoder import GoogleGeocoder


def get_raw_data():
    path = os.path.join(os.path.dirname(__file__), 'data', '2011.csv')
    return list(csv.DictReader(open(path, 'r')))


def get_mapped_data():
    path = os.path.join(os.path.dirname(__file__), 'data', '2011_geocoded.csv')
    return list(csv.DictReader(open(path, 'r')))

def geocode():
    data = get_raw_data()
    geocoder = GoogleGeocoder()
    outpath = os.path.join(os.path.dirname(__file__), 'data', '2011_geocoded.csv')
    outfile = csv.writer(open(outpath, "w"))
    outfile.writerow(['Name', 'Address', 'Time', 'Date', 'Lat', 'Lng'])
    for row in data:
        address = row.get("Address")
        print address
        search = geocoder.get(address, region='US')
        coords = search[0].geometry.location
        row['lat'], row['lng'] = coords.lat, coords.lng
        outfile.writerow([
            row['Name'],
            row['Address'],
            row['Time'],
            row['Date'],
            row['lat'],
            row['lng'],
        ])


def model():
    [i.delete() for i in FreeFluVaccine.objects.all()]
    data = get_mapped_data()
    for i in data:
        FreeFluVaccine.objects.create(
            name=i.get("Name"),
            address=i.get("Address"),
            date=parse(i.get("Date")),
            time_range=i.get("Time"),
            latitude=i.get("Lat"),
            longitude=i.get("Lng"),
        )

