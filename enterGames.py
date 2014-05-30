#!/usr/bin/python
import os
import string
import sys
import copy
import time
import datetime
import dateutil.parser
import urllib, urllib2


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
    origCurrTime = currTime
    while True:
        prompt = "Enter the game date [%s]" % str(currDate)
        gameDate = raw_input("%s: " % prompt)
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
            currTime = origCurrTime
        else:
            return d

def getName(players, promptText="Enter name"):
    while True:
        enteredName = raw_input("%s: " % promptText)
        enteredName = enteredName.strip()
        if players.has_key(enteredName.lower()):
            name = players[enteredName.lower()][:]
            while name[-1] in ['"', ' ', '\n']:
                name = name[:-1]
            return name
        candidates = [player[1] for player in players.items() if enteredName.lower() == player[0][:len(enteredName)]]
        if len(set(candidates)) == 1:
            name = candidates[0][:]
            while name[-1] in ['"', ' ', '\n']:
                name = name[:-1]
            return name
        elif len(candidates) == 0:
            candidates = [player[1] for player in players.items() if enteredName.lower()[:len(player[0])] == player[0]]
        if len(candidates) > 0:
            print("Candidate players are: %s" % str(candidates))
        enteredName = standardizeCase(enteredName)
        newName = raw_input("Is '%s' a new name to be added? " % enteredName)
        if newName.upper() == 'Y' or newName.upper == 'YES':
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
    try:
        gameDate = getDate(prevDate)
        winFront = getName(players, promptText="Name of the Front Winner")
        winBack = getName(players, promptText=" Name of the Back Winner")
        loseFront = getName(players, promptText=" Name of the Front Loser")
        loseBack = getName(players, promptText="  Name of the Back Loser")
        winPoints = getPoints(" Enter number of games won: ")
        losePoints = getPoints("Enter number of games lost: ")
    except:
        return (None, None)

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
    gameCount = 0
    ofile = open(outFileName, 'w')
    while True:
        game, gameDate = enterGame(players, gameDate)
        if game is None:
            print("---Break detected!---")
            break
        gameCount += 1
        gameData = "%(date)s,%(front_winner)s,%(back_winner)s,%(front_loser)s,%(back_loser)s,%(win_points)d,%(lose_points)d\n" % game
        print gameData, #!!!
        ofile.write(gameData)
    ofile.close()
    return gameCount

def backupAllGames(url='http://elo-foosball.appspot.com/download'):
    today = datetime.datetime.today()
    backupFilename = today.strftime("Foosball_%Y%m%d.bak")
    if not os.path.exists(backupFilename):
        print("Backing up all of the current Foosball scores to: %s" % backupFilename)
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        backup_data = response.read()
        bkupFile = open(backupFilename, 'w')
        bkupFile.write(backup_data.replace('\r', ''))
        bkupFile.close()

if __name__ == '__main__':
    outFileName = 'newgames.csv'
    playerFile = 'foosballPlayers.txt'
    if len(sys.argv) > 1:
        outFileName = sys.argv[1]
        if len(sys.argv) > 2:
            playerFile = sys.argv[2]
    backupAllGames("http://elo-foosball.appspot.com/download")
    players = loadPlayerData(playerFile)
    players0 = copy.copy(players)
    numGames = addGames(players, outFileName)
    if players != players0:
        print("The list of known players has been updated.")
        writePlayerData(playerFile, players)
    print
    if numGames > 0:
        print
        print("%d games have been entered." % numGames)
        print
        print("Please go to the URL: http://elo-foosball.appspot.com/upload")
        print("and choose the file: %s and \"Submit Score\"." % os.path.join(os.path.realpath('.'), outFileName))
        print
        print("It is important that you do this before the next time you run this program")
        print("\tor your current entries will lost!")
    else:
        print("No games were entered.")
    time.sleep(3)

