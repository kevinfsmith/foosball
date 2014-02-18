import os
import string
import sys
import csv
import dateutil.parser


AllNames = {
    "Avi": "Avi",
    "Bill": "Bill",
    "Brian": "Brian",
    "Brittany": "Brittany",
    "Cary": "Cary",
    "Chay": "Chhay",
    "Chhay": "Chhay",
    "Chris": "Chris",
    "Cliff": "Cliff",
    "Dan": "Dan",
    "Dave": "Dave",
    "Dave R": "Dave R",
    "David": "David",
    "Don": "Don",
    "Erin": "Erin",
    "Ezra": "Ezra",
    "Ivan": "Ivan",
    "James": "James",
    "Jenna": "Jenna",
    "Jim": "Jim",
    "John M": "John M",
    "John V": "John V",
    "Karl": "Karl",
    "Kelly": "Kelly",
    "Kevin": "Kevin",
    "Luis": "Luis",
    "Marc": "Marc",
    "Mark": "Mark T",
    "Mark T": "Mark T",
    "Megha": "Megha",
    "Mike": "Mike B",
    "Mike B": "Mike B",
    "Miles": "Miles",
    "Noel": "Noel",
    "Oren": "Oreng",
    "Oreng": "Oreng",
    "Paul D": "Paul D",
    "Rakin": "Rakin",
    "Richard": "Richard",
    "Rob": "Rob",
    "Robert": "Robert",
    "Ron": "Ron",
    "Shack": "Shack",
    "Shital": "Shital",
    "Stephen": "Stephen",
    "Steve D": "Steve D",
    "Stuart": "Stuart",
    "Sumeet": "Sumeet",
    "Taison": "Taison",
    "Tulio": "Tullio",
    "Tullio": "Tullio",
    "Victor": "Victor",
    "Vish": "Vishwas",
    "Vishwas": "Vishwas",
}

ENTERED_SCORES_HEADERS  = ['date', 'winFront', 'winBack', 'loseFront', 'loseBack', 'gameScore']
PREPARED_SCORES_HEADERS = ['date', 'winFront', 'winBack', 'loseFront', 'loseBack', 'winPoints', 'lostPoints']


def addName(name, names=AllNames):
    if not names.has_key(name):
        names[name] = name
        return True
    return False
    
def collectAllNames(infile, outfile=None, headers=ENTERED_SCORES_HEADERS):
    allNames = {}
    scores = csv.DictReader(open(infile).readlines(), headers)
    ofile = open(outfile, 'w')
    for score in scores:
        if score['date']:
            score['date'] = score['date'].strip()
            if score['date'][0] not in string.digits:
                continue
        addName(score['winFront'], allNames)
        addName(score['winBack'], allNames)
        addName(score['loseFront'], allNames)
        addName(score['loseBack'], allNames)
    names = allNames.keys()
    names.sort()
    if outfile is not None:
        ofile = open(outfile, 'w')
        ofile.write("AllNames = {\n")
        for name in names:
            ofile.write("    \"%s\": \"%s\",\n" % (name, allNames[name]))
        ofile.write("}\n")
    return names

def validatedName(playerName, names=AllNames):
    name = playerName.strip()
    if not names.has_key(name):
        print("Unknown name: '%s'" % name)
        raise ValueError("Unknown name: '%s'" % name)
    return names[name]

def prepareScoreFormat(infile, outfile):
    currentTime = 0
    scores = csv.DictReader(open(infile).readlines(), ENTERED_SCORES_HEADERS)
    ofile = open(outfile, 'w')
    lineNumber = 0
    for score in scores:
        lineNumber += 1
        if score['date']:
            score['date'] = score['date'].strip()
            if score['date'][0] not in string.digits:
                continue
            currentDate = score['date']
            currentTime = 0
        if not score['gameScore'] or score['gameScore'].strip()[0] not in string.digits:
            continue
        i = score['gameScore'].find('-')
        winPoints = lostPoints = 0
        if i > 0:
            winPoints = int(score['gameScore'][:i])
        losePoints = int(score['gameScore'][i+1:])
        preparedDate = currentDate + " %02d:00:00" % currentTime
        try:
            preparedScore = {
                            'date': preparedDate, 
                             'front_winner': validatedName(score['winFront']),
                             'back_winner': validatedName(score['winBack']),
                             'front_loser': validatedName(score['loseFront']),
                             'back_loser': validatedName(score['loseBack']),
                             'win_points': winPoints,
                             'lose_points': losePoints,
                             }
        except ValueError as errMsg:
            #print("%s" % errMsg)
            print("Line #%d: %s" % (lineNumber, str(score)))
            print
            raise
        ofile.write("%(date)s,%(front_winner)s,%(back_winner)s,%(front_loser)s,%(back_loser)s,%(win_points)d,%(lose_points)d\n" % preparedScore)
        currentTime += 1
    ofile.close()

if __name__ == '__main__':
    inName = 'games.csv'
    outName = 'webgames.csv'
    if len(sys.argv) > 1:
        inName = sys.argv[1]
        if len(sys.argv) > 2:
            outName = sys.argv[2]
#    collectAllNames(inName, outName, ENTERED_SCORES_HEADERS)
#    collectAllNames(inName, outName, PREPARED_SCORES_HEADERS)
    prepareScoreFormat(inName, outName)

