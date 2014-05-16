import os
import string
import sys
import csv
import dateutil.parser


AllNames = {
    "Al": "Al",
    "Al B": "Al",
    "Avi A": "Avi A",
    "Avi M": "Avi M",
    "Bill": "Bill",
    "Bill G": "Bill",
    "Brian": "Brian J",
    "Brian J": "Brian J",
    "Brit": "Brittany",
    "Britt": "Brittany",
    "Brittany": "Brittany",
    "Cary": "Cary",
    "Chai": "Chhay",
    "Chay": "Chhay",
    "Chhay": "Chhay",
    "Chris": "Chris A",
    "Chris A": "Chris A",
    "Chris A.": "Chris A",
    "Cliff": "Cliff",
    "Dan P": "Dan P",
    "Dan S": "Dan S",
    "Dan Sal": "Dan S",
    "Dave S": "Shack",
    "Dave":   "Dave R",
    "Dave R": "Dave R",
    "David N": "David N",
    "Don": "Don H",
    "Don H": "Don H",
    "Eric L": "Eric L",
    "Erin": "Erin R",
    "Erin R": "Erin R",
    "Ezra": "Ezra",
    "Ivan": "Ivan",
    "Jaynika": "Jaynika",
    "James C": "James C",
    "Jenna": "Jenna",
    "Jim": "Jim",
    "Jim G": "Jim G",
    "Jim W": "Jim",
    "John B": "John B",
    "John M": "John M",
    "John V": "John V",
    "Julius": "Julius",
    "Carl": "Karl",
    "Karl": "Karl",
    "Kelly": "Kelly",
    "Kevin": "Kevin",
    "Luis": "Luis",
    "Marc": "Marc",
    "Mark M": "Mark M",
    "Mark T": "Mark T",
    "Matt": "Matt",
    "Megha": "Megha",
    "Mike B": "Mike B",
    "Mike P": "Mike P",
    "Miles": "Miles",
    "Nick": "Nick C",
    "Nick C": "Nick C",
    "Noel": "Noel",
    "Oren": "Oren G",
    "Oreng": "Oren G",
    "Oren G": "Oren G",
    "Paul D": "Paul D",
    "Pramit": "Pramit",
    "Rakin": "Rakin",
    "Richard": "Richard S",
    "Richard S": "Richard S",
    "Robert": "Robert H",
    "Robert H": "Robert H",
    "Ron": "Ron F",
    "Ron F": "Ron F",
    "Shack": "Shack",
    "Shital": "Shital",
    "Stephen J": "Stephen J",
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


def standardizeCase(name):
    names = name.split(' ')
    cased_name = []
    for n in names:
        if n:
            cased_name.append(n[0].upper() + n[1:].lower())
    name = ' '.join(cased_name)
    return name

def addName(name, names=AllNames):
    name = standardizeCase(name)
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
    name = standardizeCase(name)
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

