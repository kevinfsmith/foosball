#!/usr/bin/env python

import fileinput
import math
from sys import stdout, stdin
from datetime import datetime, date
from os import environ
from collections import defaultdict
from argparse import ArgumentParser, FileType
from Cheetah.Template import Template

def foosball_cli():
	parser = ArgumentParser(description='Calculate Elo rankings from foosball game results')
	parser.add_argument('-K', metavar='K', type=int, default=50)
	parser.add_argument('-S', '--start-rating', metavar='S', type=int, default=750)
	parser.add_argument('-f', '--fractional', action='store_true')
	parser.add_argument('-l', '--limit', type=int, default=0)
	parser.add_argument('-o', '--output', type=FileType('w'), default=stdout)
	parser.add_argument('games', nargs='?', type=FileType('r'), default=stdin)
	args = parser.parse_args()
	
	foosball_common(vars(args))

def foosball_cgi():
	import cgitb
	print "Content-Type: text/html; charset=utf-8\r\n\r\n",
	cgitb.enable()
	import cgi
	fs = cgi.FieldStorage()
	args = {
		"K":50,
		"start_rating":750,
		"fractional":False,
		"limit":0,
		"output": stdout
	}
	if not fs.has_key("games"):
		print """
<html>
<body>
<form method="POST" enctype="multipart/form-data" action="">
<input type="file" name="games" />
<input type="submit" />
</form>
</body>
</html>
"""
		return 1
	for k in fs:
		if fs[k].file is None:
			args[k] = fs[k].value
		else:
			args[k] = fs[k].file
	foosball_common(args)

def foosball_common(args):
	combined=defaultdict(lambda: args["start_rating"])
	front=defaultdict(lambda: args["start_rating"])
	back=defaultdict(lambda: args["start_rating"])
	front_played=defaultdict(lambda: 0)
	back_played=defaultdict(lambda: 0)

	combined_history = defaultdict(lambda: [])
	front_history = defaultdict(lambda: [])
	back_history = defaultdict(lambda: [])

	games = []
	last_date = date.min

	for game in args["games"]:
		games.append(game.strip().split("\t"))
		games[-1].append(len(games))
		this_date, winner1, winner2, loser1, loser2, win_points, lose_points, game_number = games[-1]
		this_date=datetime.strptime(this_date,"%d/%m/%Y").date()
		last_date = max(this_date, last_date)
		front_played[winner1] += 1
		back_played[winner2] += 1
		front_played[loser1] += 1
		back_played[loser2] += 1
		win_points=int(win_points)
		lose_points = int(lose_points)
		D = combined[loser1] + combined[loser2] - combined[winner1] - combined[winner2]
		E = 1.0 / (1+math.pow(10,D/800.0))
		if args["fractional"]:
			points = args["K"]*(float(win_points)/(win_points+lose_points)-E)
		else:
			points = args["K"]*(1-E)*(win_points-lose_points)
		points = int(round(points))
		combined[winner1] += points
		combined[winner2] += points
		combined[loser1] -= points
		combined[loser2] -= points
		combined_history[winner1].append((combined[winner1], points, -D, E, game_number))
		combined_history[winner2].append((combined[winner2], points, -D, E, game_number))
		combined_history[loser1].append((combined[loser1], -points, D, 1-E, game_number))
		combined_history[loser2].append((combined[loser2], -points, D, 1-E, game_number))

		D = front[loser1] + back[loser2] - front[winner1] - back[winner2]
		E = 1.0 / (1+math.pow(10,D/800.0))
		if args["fractional"]:
			points = args["K"]*(float(win_points)/(win_points+lose_points)-E)
		else:
			points = args["K"]*(1-E)*(win_points-lose_points)
		points = int(round(points))
		front[winner1] += points
		back[winner2] += points
		front[loser1] -= points
		back[loser2] -= points
		front_history[winner1].append((front[winner1], points, -D, E, game_number))
		front_history[loser1].append((front[loser1], -points, D, 1-E, game_number))
		back_history[winner2].append((back[winner2], points, -D, E, game_number))
		back_history[loser2].append((back[loser2], -points, D, 1-E, game_number))

	player_output = []
	for player in sorted(combined.keys()):
		fronts = ""
		if player in front and front_played[player] >= args["limit"]:
			fronts = str(front[player])
		backs = ""
		if player in back and back_played[player] >= args["limit"]:
			backs = str(back[player])
		combineds = ""
		if front_played[player]+back_played[player] >= args["limit"]:
			combineds = str(combined[player])
		player_output.append((player,combineds,fronts, backs))

	templateDef = """<!DOCTYPE html>
	<html>
	<head>
		<meta charset="UTF-8" />
		<script src="js/jquery.min.js" type="text/javascript"></script>
		<link href="css/jquery-ui.min.css" rel="stylesheet" type="text/css"/>
		<script src="js/jquery-ui.min.js" type="text/javascript"></script>
		<script src="js/bootstrap.min.js" type="text/javascript"></script>
		<link href="css/bootstrap.min.css" rel="stylesheet" type="text/css"/>
		<script src="js/jquery.tablesorter.min.js" type="text/javascript"></script>
		<script src="js/jquery.tablesorter.widgets.min.js" type="text/javascript"></script>
		<script src="js/js-class.js" type="text/javascript"></script>
		<script src="js/bluff-min.js" type="text/javascript"></script>
		<link href="css/theme.bootstrap.css" rel="stylesheet" type="text/css"/>
		<style type="text/css">
		body {
			padding-top: 60px;
		}
		</style>
		<script type="text/javascript">

	  function tablesorter(table_name) {
		\$(table_name).tablesorter({
			theme:"bootstrap",
			headerTemplate: '{content} {icon}',
			widgets: ["uitheme"]
		});
	  }
	  \$(function() {
		\$.extend(\$.tablesorter.themes.bootstrap, {
			sortNone: "bootstrap-icon-unsorted",
			sortAsc: "icon-chevron-up",
			sortDesc: "icon-chevron-down"
		});
		\$("#players").accordion({ active: false , collapsible: true, heightStyle: "content", icons: { "header": "ui-icon-plus", "headerSelected": "ui-icon-minus" }});
		tablesorter("#scores");
		tablesorter("#games-table");
		var cg;
		var fg;
		var bg;
		#for $player in $player_output
			cg = new Bluff.Line('graph-comb-$player[0]', '400x300');
			cg.data_from_table('data-comb-$player[0]', options={'orientation':'cols','except':['Change','Ability Advantage','Expected Chance of Winning','Game Number']});
			cg.hide_legend=true;
			cg.theme_greyscale();
			cg.draw();
			fg = new Bluff.Line('graph-front-$player[0]', '400x300');
			fg.data_from_table('data-front-$player[0]', options={'orientation':'cols','except':['Change','Ability Advantage','Expected Chance of Winning','Game Number']});
			fg.hide_legend=true;
			fg.theme_greyscale();
			fg.draw();
			bg = new Bluff.Line('graph-back-$player[0]', '400x300');
			bg.data_from_table('data-back-$player[0]', options={'orientation':'cols','except':['Change','Ability Advantage','Expected Chance of Winning','Game Number']});
			bg.hide_legend=true;
			bg.theme_greyscale();
			bg.draw();
			tablesorter("#data-comb-$player[0]");
			tablesorter("#data-front-$player[0]");
			tablesorter("#data-back-$player[0]");
		#end for
	  });
		</script>
		<title>Foosball Scores - $last_date</title>
	</head>
	<body>
	<div class="navbar navbar-fixed-top">
		<div class="navbar-inner">
			<a class="brand" href="#">Foosball Scores</a>
			<ul class="nav">
				<li><a href="#scores">Scores</a></li>
				<li><a href="#player">Player Reports</a></li>
				<li><a href="#games">Games</a></li>
			</ul>
		</div>
	</div>
	<div class="container">
	<h2>Scores</h2>
	<div>
	<table id="scores" class="table table-striped tablesorter">
	<thead>
	<tr><th>Player</th><th>Combined Score</th><th>Front Score</th><th>Back Score</th></tr>
	</thead>
	<tbody>
		#for $player in $player_output
			<tr><td><a href="#$player[0]">$player[0]</a></td><td>$player[1]</td><td>$player[2]</td><td>$player[3]</td></tr>
		#end for
	</tbody>
	</table>
	<h2>Player Reports</h2>
	<div id="players">
		#for $player in $player_output
		<h2 id="$player[0]">$player[0]</h2>
		<div>
			<canvas id="graph-comb-$player[0]"></canvas>
			<canvas id="graph-front-$player[0]"></canvas>
			<canvas id="graph-back-$player[0]"></canvas>
			<table id="data-comb-$player[0]" class="table table-striped tablesorter">
			<caption>Combined History</caption>
			<thead>
				<tr><th>Score</th><th>Change</th><th>Ability Advantage</th><th>Expected Chance of Winning</th><th>Game Number</th></tr>
			</thead>
			<tbody>
			#for $entry in $combined_history[$player[0]]
				<tr><td>$entry[0]</td><td>$entry[1]</td><td>$entry[2]</td><td>$entry[3]</td><td><a href="#game-$entry[4]">$entry[4]</a></td></tr>
			#end for
			</tbody>
			</table>
			<table id="data-front-$player[0]" class="table table-striped">
			<caption>Front History</caption>
			<thead>
				<tr><th>Score</th><th>Change</th><th>Ability Advantage</th><th>Expected Chance of Winning</th><th>Game Number</th></tr>
			</thead>
			<tbody>
			#for $entry in $front_history[$player[0]]
				<tr><td>$entry[0]</td><td>$entry[1]</td><td>$entry[2]</td><td>$entry[3]</td><td><a href="#game-$entry[4]">$entry[4]</a></td></tr>
			#end for
			</tbody>
			</table>
			<table id="data-back-$player[0]" class="table table-striped">
			<caption>Back History</caption>
			<thead>
				<tr><th>Score</th><th>Change</th><th>Ability Advantage</th><th>Expected Chance of Winning</th><th>Game Number</th></tr>
			</thead>
			<tbody>
			#for $entry in $back_history[$player[0]]
				<tr><td>$entry[0]</td><td>$entry[1]</td><td>$entry[2]</td><td>$entry[3]</td><td><a href="#game-$entry[4]">$entry[4]</a></td></tr>
			#end for
			</tbody>
			</table>
		</div>
	#end for
	</div>
	<h2 id="games">Games</h2>
	<table class="table table-striped tablesorter" id="games-table">
	<thead>
	<tr><th>Date</th><th>Game Number</th><th>Winning Front</th><th>Winning Back</th><th>Losing Front</th><th>Losing Back</th><th>Score</th></tr>
	</thead>
	<tbody>
		#for $game in $games
			<tr id="game-$game[7]"><td>$game[0]</td><td>$game[7]</td><td>$game[1]</td><td>$game[2]</td><td>$game[3]</td><td>$game[4]</td><td>$game[5]-$game[6]</td></tr>
		#end for
	</tbody>
	<div>
	<table>
	</table>
	</div>
	</div>
	</body>
	</html>
	"""

	args["output"].write(str(Template(templateDef, {'player_output':player_output, 'combined_history':combined_history, 'front_history':front_history, 'back_history':back_history, 'games':games, 'last_date':last_date})))

if __name__ == '__main__':
	if environ.has_key('GATEWAY_INTERFACE'):
		foosball_cgi()
	else:
		foosball_cli();
