#!/usr/bin/env python

import fileinput
import math
from collections import defaultdict
from argparse import ArgumentParser

parser = ArgumentParser(description='Calculate Elo rankings from foosball game results')
parser.add_argument('-K', metavar='K', type=int, default=50)
parser.add_argument('-S', '--start-rating', metavar='S', type=int, default=750)
parser.add_argument('-f', '--fractional', action='store_true')
parser.add_argument('-s', '--stats', action='store_true')
parser.add_argument('-l', '--limit', type=int, default=0)
parser.add_argument('-p', '--player', type=str, default=None)
parser.add_argument('games', nargs='*')
args = parser.parse_args()

combined=defaultdict(lambda: args.start_rating)
front=defaultdict(lambda: args.start_rating)
back=defaultdict(lambda: args.start_rating)
front_played=defaultdict(lambda: 0)
back_played=defaultdict(lambda: 0)

combined_history = []
front_history = []
back_history = []

for game in fileinput.input(args.games):
	game = game.strip()
	winner1, winner2, loser1, loser2, win_points, lose_points = game.split("\t")
	front_played[winner1] += 1
	back_played[winner2] += 1
	front_played[loser1] += 1
	back_played[loser2] += 1
	win_points=int(win_points)
	lose_points = int(lose_points)
	D = combined[loser1] + combined[loser2] - combined[winner1] - combined[winner2]
	E = 1.0 / (1+math.pow(10,D/800.0))
	if args.fractional:
		points = args.K*(float(win_points)/(win_points+lose_points)-E)
	else:
		points = args.K*(1-E)*(win_points-lose_points)
	points = int(round(points))
	combined[winner1] += points
	combined[winner2] += points
	combined[loser1] -= points
	combined[loser2] -= points
	if args.player in (winner1, winner2):
		combined_history.append("%d (%3d D=%4d, E=%5.3g)\t%s" % (combined[args.player], points, D, E, game))
	if args.player in (loser1, loser2):
		combined_history.append("%d (%3d D=%4d, E=%5.3g)\t%s" % (combined[args.player], -points, D, E, game))

	D = front[loser1] + back[loser2] - front[winner1] - back[winner2]
	E = 1.0 / (1+math.pow(10,D/800.0))
	if args.fractional:
		points = args.K*(float(win_points)/(win_points+lose_points)-E)
	else:
		points = args.K*(1-E)*(win_points-lose_points)
	points = int(round(points))
	front[winner1] += points
	back[winner2] += points
	front[loser1] -= points
	back[loser2] -= points
	if args.player == winner1:
		front_history.append("%d (%3d D=%4d, E=%5.3g)\t%s" % (front[winner1], points, D, E, game))
	if args.player == loser1:
		front_history.append("%d (%3d D=%4d, E=%5.3g)\t%s" % (front[loser1], -points, D, E, game))
	if args.player == winner2:
		back_history.append("%d (%3d D=%4d, E=%5.3g)\t%s" % (back[winner2], points, D, E, game))
	if args.player == loser2:
		back_history.append("%d (%3d D=%4d, E=%5.3g)\t%s" % (back[loser2], -points, D, E, game))

for player in sorted(combined.keys()):
	fronts = ""
	if player in front and front_played[player] >= args.limit:
		fronts = str(front[player])
	backs = ""
	if player in back and back_played[player] >= args.limit:
		backs = str(back[player])
	combineds = ""
	if front_played[player]+back_played[player] >= args.limit:
		combineds = str(combined[player])
	print "%s\t%s\t%s\t%s" % (player,combineds,fronts, backs)

SS_unified=0.0
SS_unified_f=0.0
SS_separated=0.0
SS_separated_f=0.0

if args.stats:
	for game in fileinput.input(args.games):
		game = game.strip()
		winner1, winner2, loser1, loser2, win_points, lose_points = game.split("\t")
		win_points=int(win_points)
		lose_points = int(lose_points)
		D = combined[loser1] + combined[loser2] - combined[winner1] - combined[winner2]
		E = 1.0 / (1+math.pow(10,D/800.0))
		SS_unified_f += (float(win_points)/(win_points+lose_points)-E)**2
		SS_unified += (1-E)*(win_points-lose_points)**2
		D = front[loser1] + back[loser2] - front[winner1] - back[winner2]
		E = 1.0 / (1+math.pow(10,D/800.0))
		SS_separated_f += (float(win_points)/(win_points+lose_points)-E)**2
		SS_separated += (1-E)*(win_points-lose_points)**2
	print "SSU: ", SS_unified
	print "SSS: ", SS_unified
	print "SSU_f: ", SS_unified_f
	print "SSS_f: ", SS_unified_f

if args.player is not None:
	print "Combined Rating History:"
	for game in combined_history:
		print " %s" % game
	print "\nFront Rating History:"
	for game in front_history:
		print " %s" % game
	print "\nBack Rating History:"
	for game in back_history:
		print " %s" % game
