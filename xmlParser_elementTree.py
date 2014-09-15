from itertools import imap, islice, izip
from operator  import itemgetter
from xml.etree.ElementTree import iterparse, XMLParser
from StatNewsWriter import DatabaseController, StatNewsWriterInterface
import htmlentitydefs
import datetime
import calendar
import nltk, string

class CustomEntity:
    def __getitem__(self, key):
        if key == 'umml':
            key = 'uuml' # Fix invalid entity
        return unichr(htmlentitydefs.name2codepoint[key])

parser = XMLParser()
parser.parser.UseForeignDTD(True)
parser.entity = CustomEntity()

records = []
count = 0

it = imap(itemgetter(1), iter(iterparse('./input/dblp.xml', events=['start'], parser=parser)));
root = next(it)
dbc = DatabaseController('./output/dblp_full.db')
db = StatNewsWriterInterface(dbc)

for node in it:
    if (node.tag == 'article'):
        count = count + 1
        if (count % 1000 == 0):
            print count
        # if (count > 3000):
        #     break
        # print '=' * 50
        # print node.attrib['mdate']
        dateContent = node.attrib['mdate']
        dateTime = datetime.datetime.strptime(dateContent, "%Y-%m-%d")
        unixTime = calendar.timegm(dateTime.utctimetuple())
        # print unixTime

        paperTitle = ''
        paperSource = ''
        for child in node:
            # print child.tag
            if (child.tag == 'title'):
                # print child.text
                paperTitle = child.text
            if (child.tag == 'journal'):
                # print child.text
                paperSource = child.text

        if (paperTitle == None or paperSource == None):
            continue

        if len(paperTitle) <= 10 and len(paperTitle) > 0:
            continue

        doc = {}
        doc['content'] = paperTitle
        doc['source'] = paperSource
        doc['title'] = paperTitle
        doc['time'] = unixTime
        db.writeDataHandler(data=[doc])
        records.append(doc)

    root.clear()

print 'Total:', len(records)
# db.writeDataHandler(data=records)
