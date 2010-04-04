"""
A one-off routine for merging a CSV of explanations against the Category model.
"""
import csv
from data.models import Category

def merge():
    table = csv.reader(open('./toolbox/data/explanations.csv', "rU"), dialect=csv.excel_tab, quotechar='"', delimiter=',') 
    for i, row in enumerate(table):
        name, explanation = row
        try: 
            c = Category.objects.get(name__iexact=name)
            c.explanation = explanation
            c.save()
        except:
            print "NO", name
