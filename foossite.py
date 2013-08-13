#!/usr/bin/env python

import fileinput
import math
import itertools
from sys import stdout, stdin
from datetime import datetime, date, time, timedelta
from os import environ, path
from collections import defaultdict
from argparse import ArgumentParser, FileType
from Cheetah.Template import Template

date_format = "%Y/%m/%d"

def last(list, fun, default=None):
	prev = default
	for i in list:
		if not fun(i):
			return prev
		prev = i
	return prev

def drange(start, end, step):
	i = start
	while i < end:
		yield i
		i = i + step

def drange_with_end(start, end, step):
	i = start
	while i < end:
		yield i
		i = i + step
	if i != end:
		yield end

def todate(d):
	if type(d) == datetime:
		return d.date()
	else:
		return d

def foosball_cli():
	parser = ArgumentParser(description='Calculate Elo rankings from foosball game results')
	parser.add_argument('-K', metavar='K', type=int, default=50)
	parser.add_argument('-S', '--start-rating', metavar='S', type=int, default=750)
	parser.add_argument('-f', '--fractional', action='store_true')
	parser.add_argument('-m', '--match', action='store_true')
	parser.add_argument('-l', '--limit', type=int, default=0)
	parser.add_argument('-o', '--output', default='output')
	parser.add_argument('games', nargs='?', type=FileType('r'), default=stdin)
	args = parser.parse_args()
	
	foosball_common(vars(args))

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
		this_date=datetime.strptime(this_date,date_format).date()
		last_date = max(this_date, last_date)
		front_played[winner1] += 1
		back_played[winner2] += 1
		front_played[loser1] += 1
		back_played[loser2] += 1
		win_points=int(win_points)
		lose_points = int(lose_points)
		D = combined[loser1] + combined[loser2] - combined[winner1] - combined[winner2]
		E = 1.0 / (1+math.pow(10,D/800.0))
		E_reverse = 1.0 / (1+math.pow(10,-D/800.0))
		if args["fractional"]:
			points = args["K"]*(float(win_points)/(win_points+lose_points)-E)
		elif args["match"]:
			points = args["K"]*(1-E)*(win_points-lose_points)
		else:
			points = args["K"]*((1-E)*win_points-(1-E_reverse)*lose_points)
		points = int(round(points))
		combined[winner1] += points
		combined[winner2] += points
		combined[loser1] -= points
		combined[loser2] -= points
		combined_history[winner1].append([combined[winner1], points, -D, E, game_number, this_date])
		combined_history[winner2].append([combined[winner2], points, -D, E, game_number, this_date])
		combined_history[loser1].append([combined[loser1], -points, D, 1-E, game_number, this_date])
		combined_history[loser2].append([combined[loser2], -points, D, 1-E, game_number, this_date])

		D = front[loser1] + back[loser2] - front[winner1] - back[winner2]
		E = 1.0 / (1+math.pow(10,D/800.0))
		E_reverse = 1.0 / (1+math.pow(10,-D/800.0))
		if args["fractional"]:
			points = args["K"]*(float(win_points)/(win_points+lose_points)-E)
		elif args["match"]:
			points = args["K"]*(1-E)*(win_points-lose_points)
		else:
			points = args["K"]*((1-E)*win_points-(1-E_reverse)*lose_points)
		points = int(round(points))
		front[winner1] += points
		back[winner2] += points
		front[loser1] -= points
		back[loser2] -= points
		front_history[winner1].append([front[winner1], points, -D, E, game_number, this_date])
		front_history[loser1].append([front[loser1], -points, D, 1-E, game_number, this_date])
		back_history[winner2].append([back[winner2], points, -D, E, game_number, this_date])
		back_history[loser2].append([back[loser2], -points, D, 1-E, game_number, this_date])

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

		#Fudge date so games aren't all at the same time
		for history in combined_history, front_history, back_history:
			last_seen_date = date.min
			last_seen_count = 0
			for i in xrange(len(history[player])):
				if history[player][i][5] == last_seen_date:
					last_seen_count += 2
					history[player][i][5] = datetime.combine(last_seen_date, time(last_seen_count))
				else:
					last_seen_date = history[player][i][5] 
					last_seen_count = 0
	
	weekly_combined_scores = [(when,{player : last(combined_history[player], lambda x: todate(x[5]) < when,[args["start_rating"]])[0] for player in combined.keys()}) for when in drange_with_end(datetime.strptime(games[0][0],date_format).date(), datetime.strptime(games[-1][0],date_format).date(), timedelta(7))]
	weekly_combined_ranks = [(when,sorted(player_scores.keys(),key=lambda x:player_scores[x])) for (when,player_scores) in weekly_combined_scores]
	player_weekly_combined_ranks =  {player:
		[[when,rank.index(player)] for (when,rank) in weekly_combined_ranks]
		for player in combined.keys()
	}

	weekly_front_scores = [(when,{player : last(front_history[player], lambda x: todate(x[5]) < when,[args["start_rating"]])[0] for player in front.keys()}) for when in drange_with_end(datetime.strptime(games[0][0],date_format).date(), datetime.strptime(games[-1][0],date_format).date(), timedelta(7))]
	weekly_front_ranks = [(when,sorted(player_scores.keys(),key=lambda x:player_scores[x])) for (when,player_scores) in weekly_front_scores]
	player_weekly_front_ranks =  {player:
		[[when,rank.index(player)] for (when,rank) in weekly_front_ranks]
		for player in front.keys()
	}

	weekly_back_scores = [(when,{player : last(back_history[player], lambda x: todate(x[5]) < when,[args["start_rating"]])[0] for player in back.keys()}) for when in drange_with_end(datetime.strptime(games[0][0],date_format).date(), datetime.strptime(games[-1][0],date_format).date(), timedelta(7))]
	weekly_back_ranks = [(when,sorted(player_scores.keys(),key=lambda x:player_scores[x])) for (when,player_scores) in weekly_back_scores]
	player_weekly_back_ranks =  {player:
		[[when,rank.index(player)] for (when,rank) in weekly_back_ranks]
		for player in back.keys()
	}

	matchups = defaultdict(lambda: 0)
	for game in games:
		if matchups.has_key(((game[1], game[2]), (game[3], game[4]))):
			matchups[((game[1], game[2]), (game[3], game[4]))] += 1
		else:
			matchups[((game[3], game[4]), (game[1], game[2]))] += 1

	indexTemplate = """<!DOCTYPE html>
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
		<!--[if lt IE 9]>
			<script language="javascript" type="text/javascript" src="js/excanvas.min.js"></script>
		<![endif]-->
		<script language="javascript" type="text/javascript" src="js/jquery.jqplot.min.js"></script>
<script type="text/javascript" src="js/plugins/jqplot.dateAxisRenderer.min.js"></script>
		<script type="text/javascript" src="js/plugins/jqplot.pointLabels.min.js"></script>
		<link rel="stylesheet" type="text/css" href="css/jquery.jqplot.min.css" />
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
		$.jqplot('graph-combined', [
			[
			#for $player in $player_weekly_combined_ranks
				['$player_weekly_combined_ranks[$player][0][0]', $player_weekly_combined_ranks[$player][0][1], '$player'],
			#end for
			],
		#for $player in $player_weekly_combined_ranks
			[
			#for $rank in $player_weekly_combined_ranks[$player]
				['$rank[0]', $rank[1]],
			#end for
			],
		#end for
			[
			#for $player in $player_weekly_combined_ranks
				['$player_weekly_combined_ranks[$player][-1][0]', $player_weekly_combined_ranks[$player][-1][1], '$player'],
			#end for
			]
		], {
			title: 'Weekly Combined Rankings',
			axes:{xaxis:{renderer:$.jqplot.DateAxisRenderer}, yaxis:{tickOptions:{show:false}}},
			seriesDefaults: {shadow: false, markerOptions:{show: false}},
			series: [
				{show:false,pointLabels:{show:true, location:'w'}},
			#for $player in $player_weekly_combined_ranks
				{label:'$player'},
			#end for
				{show:false,pointLabels:{show:true, location:'e'}}
			]
		});
		$.jqplot('graph-front', [
			[
			#for $player in $player_weekly_front_ranks
				['$player_weekly_front_ranks[$player][0][0]', $player_weekly_front_ranks[$player][0][1], '$player'],
			#end for
			],
		#for $player in $player_weekly_front_ranks
			[
			#for $rank in $player_weekly_front_ranks[$player]
				['$rank[0]', $rank[1]],
			#end for
			],
		#end for
			[
			#for $player in $player_weekly_front_ranks
				['$player_weekly_front_ranks[$player][-1][0]', $player_weekly_front_ranks[$player][-1][1], '$player'],
			#end for
			]
		], {
			title: 'Weekly Front Rankings',
			axes:{xaxis:{renderer:$.jqplot.DateAxisRenderer}, yaxis:{tickOptions:{show:false}}},
			seriesDefaults: {shadow: false, markerOptions:{show: false}},
			series: [
				{show:false,pointLabels:{show:true, location:'w'}},
			#for $player in $player_weekly_front_ranks
				{label:'$player'},
			#end for
				{show:false,pointLabels:{show:true, location:'e'}}
			]
		});
		$.jqplot('graph-back', [
			[
			#for $player in $player_weekly_back_ranks
				['$player_weekly_back_ranks[$player][0][0]', $player_weekly_back_ranks[$player][0][1], '$player'],
			#end for
			],
		#for $player in $player_weekly_back_ranks
			[
			#for $rank in $player_weekly_back_ranks[$player]
				['$rank[0]', $rank[1]],
			#end for
			],
		#end for
			[
			#for $player in $player_weekly_back_ranks
				['$player_weekly_back_ranks[$player][-1][0]', $player_weekly_back_ranks[$player][-1][1], '$player'],
			#end for
			]
		], {
			title: 'Weekly Back Rankings',
			axes:{xaxis:{renderer:$.jqplot.DateAxisRenderer}, yaxis:{tickOptions:{show:false}}},
			seriesDefaults: {shadow: false, markerOptions:{show: false}},
			series: [
				{show:false,pointLabels:{show:true, location:'w'}},
			#for $player in $player_weekly_back_ranks
				{label:'$player'},
			#end for
				{show:false,pointLabels:{show:true, location:'e'}}
			]
		});
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
				<li><a href="#rankings">Weekly Rankings</a></li>
				<li><a href="#games">Games</a></li>
			</ul>
		</div>
	</div>
	<div class="container">
	<h2>Scores</h2>
	<p>Click on player name for individual player report</p>
	<table id="scores" class="table table-striped tablesorter">
	<thead>
	<tr><th>Player</th><th>Combined Score</th><th>Front Score</th><th>Back Score</th></tr>
	</thead>
	<tbody>
		#for $player in $player_output
			<tr><td><a href="${player[0]}.html">$player[0]</a></td><td>$player[1]</td><td>$player[2]</td><td>$player[3]</td></tr>
		#end for
	</tbody>
	</table>
	<h2 id="rankings">Weekly Rankings</h2>
	<div id="graph-combined" style="height: 50em"></div>
	<div id="graph-front" style="height: 50em"></div>
	<div id="graph-back" style="height: 50em"></div>
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
	playerTemplate = """<!DOCTYPE html>
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
		<!--[if lt IE 9]>
			<script language="javascript" type="text/javascript" src="js/excanvas.min.js"></script>
		<![endif]-->
		<script language="javascript" type="text/javascript" src="js/jquery.jqplot.min.js"></script>
<script type="text/javascript" src="js/plugins/jqplot.dateAxisRenderer.min.js"></script>
		<link rel="stylesheet" type="text/css" href="css/jquery.jqplot.min.css" />
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
		$.jqplot('graph', [[
		#for $entry in $combined_history[$player[0]]
			['$entry[5]', $entry[0]],
		#end for
		],[
		#for $entry in $front_history[$player[0]]
			['$entry[5]', $entry[0]],
		#end for
		],[
		#for $entry in $back_history[$player[0]]
			['$entry[5]', $entry[0]],
		#end for
		]], {
			title: '$player[0]\\'s score over time',
			axes:{xaxis:{renderer:$.jqplot.DateAxisRenderer}},
			seriesDefaults: {shadow: false, markerOptions:{show: false}},
			series: [
				{label:'Combined'},
				{label:'Front'},
				{label:'Back'}
			],
			legend: {show: true}
		});
		tablesorter("#data-comb");
		tablesorter("#data-front");
		tablesorter("#data-back");
	  });
		</script>
		<title>$player[0]'s Foosball Report - $last_date</title>
	</head>
	<body>
	<div class="navbar navbar-fixed-top">
		<div class="navbar-inner">
			<a class="brand" href="index.html">Foosball Scores</a>
			<ul class="nav">
				<li><a href="index.html#scores">Scores</a></li>
				<li><a href="index.html#rankings">Weekly Rankings</a></li>
				<li><a href="index.html#games">Games</a></li>
				<li class="divider-vertical"></li>
			<a class="brand" href="#">Player Report</a>
				<li><a href="#graph">Graph</a></li>
				<li><a href="#comb">Combined History</a></li>
				<li><a href="#front">Front History</a></li>
				<li><a href="#back">Back History</a></li>
			</ul>
		</div>
	</div>
	<div class="container">
		<div id="graph"></div>
		<h2 id="comb">Combined History</h2>
		<table id="data-comb" class="table table-striped tablesorter">
			<thead>
				<tr><th>Score</th><th>Change</th><th>Ability Advantage</th><th>Expected Chance of Winning</th><th>Game Number</th></tr>
			</thead>
			<tbody>
			#for $entry in $combined_history[$player[0]]
				<tr><td>$entry[0]</td><td>$entry[1]</td><td>$entry[2]</td><td><%= int(entry[3]*100)%>%</td><td><a href="index.html#game-$entry[4]">$entry[4]</a></td></tr>
			#end for
			</tbody>
		</table>
		<h2 id="front">Front History</h2>
		<table id="data-front" class="table table-striped">
			<thead>
				<tr><th>Score</th><th>Change</th><th>Ability Advantage</th><th>Expected Chance of Winning</th><th>Game Number</th></tr>
			</thead>
			<tbody>
			#for $entry in $front_history[$player[0]]
				<tr><td>$entry[0]</td><td>$entry[1]</td><td>$entry[2]</td><td><%= int(entry[3]*100)%>%</td><td><a href="index.html#game-$entry[4]">$entry[4]</a></td></tr>
			#end for
			</tbody>
		</table>
		<h2 id="back">Back History</h2>
		<table id="data-back" class="table table-striped">
			<thead>
				<tr><th>Score</th><th>Change</th><th>Ability Advantage</th><th>Expected Chance of Winning</th><th>Game Number</th></tr>
			</thead>
			<tbody>
			#for $entry in $back_history[$player[0]]
				<tr><td>$entry[0]</td><td>$entry[1]</td><td>$entry[2]</td><td><%= int(entry[3]*100)%>%</td><td><a href="index.html#game-$entry[4]">$entry[4]</a></td></tr>
			#end for
			</tbody>
		</table>
	</div>
	</body>
	</html>
	"""
	matchupsTemplate = """<!DOCTYPE html>
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
		<!--[if lt IE 9]>
			<script language="javascript" type="text/javascript" src="js/excanvas.min.js"></script>
		<![endif]-->
		<script language="javascript" type="text/javascript" src="js/jquery.jqplot.min.js"></script>
<script type="text/javascript" src="js/plugins/jqplot.dateAxisRenderer.min.js"></script>
		<link rel="stylesheet" type="text/css" href="css/jquery.jqplot.min.css" />
		<link href="css/theme.bootstrap.css" rel="stylesheet" type="text/css"/>
		<style type="text/css">
		body {
			padding-top: 60px;
		}
		</style>
		<script type="text/javascript">
	  function update_filter() {
		var player1 = \$("#player1")[0].value;
		var player2 = \$("#player2")[0].value;
		var player3 = \$("#player3")[0].value;
		var player4 = \$("#player4")[0].value;
		players = [player1, player2, player3, player4];
		var rows = \$(".filterable");
		for (var i=0; i<rows.length; i++) {
			var cells = \$("td",rows[i]);
			var match = true;
			for (var p=0; p<players.length; p++) {
				var player_found = false;
				for (var c=0; c<cells.length; c++) {
					if (players[p] == cells[c].innerHTML) {
						player_found = true;
						break;
					}
				}
				if (player_found == false) {
					match = false;
					break;
				}
			}
			rows[i].hidden = !match;
		}
	  }

	  function clear_filter() {
		var rows = \$(".filterable");
		for (var i=0; i<rows.length; i++) {
			rows[i].hidden = false;
		}
	  }
	  \$(function() {
		\$.extend(\$.tablesorter.themes.bootstrap, {
			sortNone: "bootstrap-icon-unsorted",
			sortAsc: "icon-chevron-up",
			sortDesc: "icon-chevron-down"
		});
		\$("#matchups").tablesorter({
			theme:"bootstrap",
			headerTemplate: '{content} {icon}',
			widgets: ["uitheme"]
		});
	  });
		</script>
		<title>Foosball Matchups - $last_date</title>
	</head>
	<body>
	<div class="navbar navbar-fixed-top">
		<div class="navbar-inner">
			<a class="brand" href="index.html">Foosball Scores</a>
			<ul class="nav">
				<li><a href="index.html#scores">Scores</a></li>
				<li><a href="index.html#rankings">Weekly Rankings</a></li>
				<li><a href="index.html#games">Games</a></li>
				<li class="divider-vertical"></li>
			</ul>
		</div>
	</div>
	<div class="container">
		<h2>Matchups</h2>
		<div class="controls controls-row">
			<input type="text" class="input-medium" id="player1" />
			<input type="text" class="input-medium" id="player2" />
			<input type="text" class="input-medium" id="player3" />
			<input type="text" class="input-medium" id="player4" />
			<div class="input-append">
				<a href="#" class="btn btn-primary" onclick="update_filter()" ><i class="icon-filter"></i> Filter</a>
				<a href="#" class="btn" onclick="clear_filter()">Clear</a>
			</div>
		</div>
		<table id="matchups" class="table table-striped tablesorter">
			<thead>
				<tr><th>Front 1</th><th>Back 1</th><th>Front 2</th><th>Back 2</th><th>Games Played</th></tr>
			</thead>
			<tbody>
			#for $players in $matchups
				<tr class="filterable"><td>$players[0][0]</td><td>$players[0][1]</td><td>$players[1][0]</td><td>$players[1][1]</td><td>$matchups[$players]</td></tr>
			#end for
			</tbody>
		</table>
	</div>
	</body>
	</html>
	"""

	with open(path.join(args["output"], "index.html"),'w') as index:
		index.write(str(Template(indexTemplate, {'player_output':player_output, 'combined_history':combined_history, 'front_history':front_history, 'back_history':back_history, 'games':games, 'last_date':last_date, 'player_weekly_combined_ranks':player_weekly_combined_ranks,'player_weekly_front_ranks':player_weekly_front_ranks, 'player_weekly_back_ranks':player_weekly_back_ranks})))
	with open(path.join(args["output"], "matchups.html"),'w') as index:
		index.write(str(Template(matchupsTemplate, {'player_output':player_output, 'combined_history':combined_history, 'front_history':front_history, 'back_history':back_history, 'games':games, 'last_date':last_date, 'player_weekly_combined_ranks':player_weekly_combined_ranks,'player_weekly_front_ranks':player_weekly_front_ranks, 'player_weekly_back_ranks':player_weekly_back_ranks,'matchups':matchups})))
	for player in player_output:
		with open(path.join(args["output"], player[0]+".html"),'w') as player_page:
			player_page.write(str(Template(playerTemplate, {'player':player,'player_output':player_output, 'combined_history':combined_history, 'front_history':front_history, 'back_history':back_history, 'games':games, 'last_date':last_date})))


if __name__ == '__main__':
	foosball_cli();
