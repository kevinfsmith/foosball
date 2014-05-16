import os
import string
import sys
import copy
import time
import dateutil.parser


PREPARED_SCORES_HEADERS = ['date', 'winFront', 'winBack', 'loseFront', 'loseBack', 'winPoints', 'lostPoints']


def standardizeCase(name):
    names = name.split(' ')
    cased_name = []
    for n in names:
        if n:
            cased_name.append(n[0].upper() + n[1:].lower())
    name = ' '.join(cased_name)
    return name

def getDate(prevDateTime=None):
    MINUTES_PER_GAME_EST = 15
    if not prevDateTime:
        prevDateTime = dateutil.parser.parse(time.asctime(time.localtime(time.time() - (MINUTES_PER_GAME_EST*60))))
        currTime = prevDateTime.hour * 60 + prevDateTime.minute
    else:
        currTime = prevDateTime.hour * 60 + prevDateTime.minute + MINUTES_PER_GAME_EST
    currDate = prevDateTime.date()
    while True:
        prompt = "Enter the game date [%s]" % str(currDate)
        try:
            gameDate = raw_input("%s: " % prompt)
        except KeyboardInterrupt:
            return None
        gameDate = gameDate.strip()
        if gameDate:
            currTime = 0
        else:
            gameDate = currDate
        try:
            d = dateutil.parser.parse(str(gameDate) + " %02d:%02d:00" % divmod(currTime, 60))
        except:
            print
            print("Invalid input!  Please try again.")
            print
        else:
            return d

def getName(players, promptText="Enter name"):
    while True:
        enteredName = raw_input("%s: " % promptText)
        enteredName = enteredName.strip()
        if players.has_key(enteredName.lower()):
            return players[enteredName.lower()]
        candidates = [player[1] for player in players.items() if enteredName.lower() == player[0][:len(enteredName)]]
        print("Known candidates are: %s" % str(candidates))
        enteredName = standardizeCase(enteredName)
        newName = raw_input("Is '%s' a new name to be added? " % enteredName)
        if newName and newName[0].upper() == 'Y':
            players[enteredName.lower()] = enteredName
            print("OK, name: '%s' is being added." % enteredName)
            return enteredName
        print("'%s' was NOT entered as a new name.  Please try entering the name again." % enteredName)
        print

def getPoints(promptText):
    while True:
        points = raw_input(promptText)
        try:
            points = int(points.strip())
        except:
            print
            print("Invalid input!  Please try again.")
            print
        else:
            return points

def enterGame(players, prevDate=None):
    print
    gameDate = getDate(prevDate)
    if gameDate is None:
        return (None, None)
    winFront = getName(players, promptText="Name of the Front Winner")
    winBack = getName(players, promptText=" Name of the Back Winner")
    loseFront = getName(players, promptText=" Name of the Front Loser")
    loseBack = getName(players, promptText="  Name of the Back Loser")
    winPoints = getPoints(" Enter number of games won: ")
    losePoints = getPoints("Enter number of games lost: ")
    preparedScore = {
                    'date': str(gameDate),
                     'front_winner': winFront,
                     'back_winner': winBack,
                     'front_loser': loseFront,
                     'back_loser': loseBack,
                     'win_points': winPoints,
                     'lose_points': losePoints,
                     }
    return (preparedScore, gameDate)

def loadPlayerData(playerFileName):
    players = {}
    for line in open(playerFileName, 'r'):
        key, name = line[:-1].split(',')
        players[key[1:-1].lower()] = name[1:-1] # remove quotes
    return players

def writePlayerData(playerFileName, players):
    keys = sorted(players.keys())
    f = open(playerFileName, 'w')
    for key in keys:
        f.write('"%s","%s"\n' % (key, players[key]))
    f.close()

def addGames(players, outFileName):
    gameDate = None
    ofile = open(outFileName, 'w')
    while True:
        game, gameDate = enterGame(players, gameDate)
        if game is None:
            break
        ofile.write("%(date)s,%(front_winner)s,%(back_winner)s,%(front_loser)s,%(back_loser)s,%(win_points)d,%(lose_points)d\n" % game)
    ofile.close()

if __name__ == '__main__':
    outFileName = 'newgames.csv'
    playerFile = 'foosballPlayers.txt'
    if len(sys.argv) > 1:
        outFileName = sys.argv[1]
        if len(sys.argv) > 2:
            playerFile = sys.argv[2]
    players = loadPlayerData(playerFile)
    players0 = copy.copy(players)
    addGames(players, outFileName)
    if players != players0:
        print("The list of known players has been updated.")
        writePlayerData(playerFile, players)
    print
    print
    print("Please go to the URL: http://elo-foosball.appspot.com/upload")
    print("and choose the file: %s and \"Submit Score\"." % os.path.join(os.path.realpath('.'), outFileName))
    print
    print("It is important that you do this before the next time you run this program")
    print("\tor your current entries will lost!")
    print
    print("To backup the Foosball data: http://elo-foosball.appspot.com/download")
    time.sleep(3)

