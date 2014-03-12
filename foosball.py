import os
import math
import itertools
import csv
import dateutil.parser
from collections import namedtuple, defaultdict
import webapp2
import webapp2_extras.sessions
import jinja2
from google.appengine.ext import ndb
from google.appengine.api import memcache
import bz2
import pickle
import datetime

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True
)
K = 20
START_RATING = 750
FRACTIONAL = False
LIMIT = 0
MATCH = False
FIELD_ORDER = ['date', 'front_winner', 'back_winner', 'front_loser', 'back_loser', 'win_points', 'lose_points']

EXCLUDE_PLAYERS_AFTER_DAYS = 30         # Don't include in rankings players which haven't played in 30 days


def memcached(key):
    def decorator(fun):
        def decorated(*args, **kwargs):
            cache = memcache.get(key)
            if cache is not None:
                data = pickle.loads(bz2.decompress(cache))
            else:
                data = fun(*args, **kwargs)
                memcache.add(key, bz2.compress(pickle.dumps(data)))
            return data

        def clear_cache():
            memcache.delete(key)
        decorated.clear_cache = clear_cache
        return decorated
    return decorator


class Game(ndb.Model):
    front_winner = ndb.StringProperty()
    back_winner = ndb.StringProperty()
    win_points = ndb.IntegerProperty()
    front_loser = ndb.StringProperty()
    back_loser = ndb.StringProperty()
    lose_points = ndb.IntegerProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def from_dict(cls, d):
        return cls(
            front_winner=d['front_winner'],
            back_winner=d['back_winner'],
            front_loser=d['front_loser'],
            back_loser=d['back_loser'],
            win_points=int(d['win_points']),
            lose_points=int(d['lose_points']),
            date=dateutil.parser.parse(d['date']),
        )

Player = namedtuple('Player', ['points', 'game'])
Ranking = namedtuple('Ranking', ['game', 'ranking'])
PlayerHist = namedtuple('PlayerHist', ['front', 'back', 'combined'])
RankingHist = namedtuple('RankingHist', ['front', 'back', 'combined'])


def elo(D, win_points, lose_points):
    E = 1.0 / (1+math.pow(10, D/800.0))
    E_reverse = 1.0 / (1+math.pow(10, -D/800.0))
    if FRACTIONAL:
        return int(K*(float(win_points)/(win_points+lose_points)-E))
    elif MATCH:
        return int(K*(1-E)*(win_points-lose_points))
    else:
        return int(K*((1-E)*win_points-(1-E_reverse)*lose_points))


def player_points(players, player, position):
    try:
        return getattr(players[player], position)[-1].points
    except IndexError:
        return START_RATING


def process_game(players, game):
    combined_point_change = elo(
        D=(player_points(players, game.front_loser, 'combined')+player_points(players, game.back_loser, 'combined') -
           player_points(players, game.front_winner, 'combined')-player_points(players, game.back_winner, 'combined')),
        win_points=game.win_points,
        lose_points=game.lose_points
    )
    point_change = elo(
        D=(player_points(players, game.front_loser, 'front')+player_points(players, game.back_loser, 'back') -
           player_points(players, game.front_winner, 'front')-player_points(players, game.back_winner, 'back')),
        win_points=game.win_points,
        lose_points=game.lose_points
    )

    players[game.front_winner].combined.append(Player(
        game=game,
        points=player_points(players, game.front_winner, 'combined')+combined_point_change
    ))
    players[game.back_winner].combined.append(Player(
        game=game,
        points=player_points(players, game.back_winner, 'combined')+combined_point_change
    ))
    players[game.front_loser].combined.append(Player(
        game=game,
        points=player_points(players, game.front_loser, 'combined')-combined_point_change
    ))
    players[game.back_loser].combined.append(Player(
        game=game,
        points=player_points(players, game.back_loser, 'combined')-combined_point_change
    ))
    players[game.front_winner].front.append(Player(
        game=game,
        points=player_points(players, game.front_winner, 'front')+point_change
    ))
    players[game.back_winner].back.append(Player(
        game=game,
        points=player_points(players, game.back_winner, 'back')+point_change
    ))
    players[game.front_loser].front.append(Player(
        game=game,
        points=player_points(players, game.front_loser, 'front')-point_change
    ))
    players[game.back_loser].back.append(Player(
        game=game,
        points=player_points(players, game.back_loser, 'back')-point_change
    ))


def update_rankings(rankings, players, game):
    rankings.front.append(
        Ranking(game, map(lambda x: x[0],
            sorted(filter(lambda x: len(x[1].front) > 0,
                          players.iteritems()),
                   key=lambda x: x[1].front[-1].points))))
    rankings.back.append(
        Ranking(game, map(lambda x: x[0],
            sorted(filter(lambda x: len(x[1].back) > 0,
                          players.iteritems()),
                   key=lambda x: x[1].back[-1].points))))
    rankings.combined.append(
        Ranking(game, map(lambda x: x[0],
            sorted(filter(lambda x: len(x[1].combined) > 0,
                          players.iteritems()),
                   key=lambda x: x[1].combined[-1].points))))


def ioffset(it, n=1):
    """Iterate pairs of each element and the previous one."""
    a, b = itertools.tee(it, 2)
    off = itertools.islice(b, n, None)
    return itertools.izip(off, a)


def weekly_rankings(rankings):
    return RankingHist(
        [x[1] for x in ioffset(rankings.front) if x[0].game.date.weekday() < x[1].game.date.weekday()] +
        [rankings.front[-1]],
        [x[1] for x in ioffset(rankings.back) if x[0].game.date.weekday() < x[1].game.date.weekday()] +
        [rankings.back[-1]],
        [x[1] for x in ioffset(rankings.combined) if x[0].game.date.weekday() < x[1].game.date.weekday()] +
        [rankings.combined[-1]],
    )


@memcached('player_rankings')
def player_rankings(rankings, players):
    return dict(
        (player, RankingHist([
            Ranking(rank.game, rank.ranking.index(player) if player in rank.ranking else None)
            for rank in rankings.front
        ], [
            Ranking(rank.game, rank.ranking.index(player) if player in rank.ranking else None)
            for rank in rankings.back
        ], [
            Ranking(rank.game, rank.ranking.index(player) if player in rank.ranking else None)
            for rank in rankings.combined
        ]
        ))
        for player in players
    )


@memcached('player_latest')
def player_latest(players):
    return dict(
        (name, (
            stats.front[-1].points if len(stats.front) > 0 else '',
            stats.back[-1].points if len(stats.back) > 0 else '',
            stats.combined[-1].points if len(stats.combined) > 0 else '',
        )) for name, stats in players.iteritems())

@memcached('processed_games')
def small_process_games():
    now = datetime.datetime.now()
    includedPlayers = set()
    players = defaultdict(lambda: PlayerHist([], [], []))
    rankings = RankingHist([], [], [])
    for game in Game.query().order(Game.date):
        if (now - game.date).days <= EXCLUDE_PLAYERS_AFTER_DAYS:
            includedPlayers.add(game.front_winner)
            includedPlayers.add(game.back_winner)
            includedPlayers.add(game.front_loser)
            includedPlayers.add(game.back_loser)
        process_game(players, game)
        update_rankings(rankings, players, game)
    players = dict(players)
    for p in players.keys():
        if p not in includedPlayers:
            del players[p]
    return (players, rankings)

def process_games():
    players, rankings = small_process_games()
    return {'players': players,
            'rankings': rankings,
            'player_latest': player_latest(players),
            'weekly_rankings': player_rankings(weekly_rankings(rankings), players)}


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = webapp2_extras.sessions.get_store(request=self.request)
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

    @webapp2.cached_property
    def messages(self):
        return self.session.get_flashes(key='_messages')

    def add_message(self, message, level=None):
        self.session.add_flash(message, level, key='_messages')

    def render_response(self, filename, **kwargs):
        if self.messages:
            kwargs['messages'] = self.messages
        self.response.write(JINJA_ENVIRONMENT.get_template(filename).render(kwargs))


class FrontPage(BaseHandler):
    def get(self):
        self.response.write(
            JINJA_ENVIRONMENT.get_template('front_page.html').render({}))

    def post(self):
        teams = [
            (
                self.request.get('front1'),
                self.request.get('back1'),
                int(self.request.get('score1')),
            ),
            (
                self.request.get('front2'),
                self.request.get('back2'),
                int(self.request.get('score2')),
            ),
        ]
        if teams[0][2] < teams[1][2]:
            teams.reverse()
        game = Game(front_winner=teams[0][0],
                    back_winner=teams[0][1],
                    win_points=teams[0][2],
                    front_loser=teams[1][0],
                    back_loser=teams[1][1],
                    lose_points=teams[1][2])
        game.put()
        small_process_games.clear_cache()
        player_rankings.clear_cache()
        player_latest.clear_cache()
        self.add_message('Game successfully recorded.', 'success')
        self.redirect('/rankings')

class RankingPage(BaseHandler):
    def get(self):
        self.render_response('ranking_page.html', **process_games())


class PlayerPage(BaseHandler):
    def get(self, player):
        kwargs = process_games()
        kwargs['player'] = player
        self.render_response('player_page.html', **kwargs)


class UploadPage(BaseHandler):
    def get(self):
        self.render_response('upload_page.html')

    def post(self):
        if self.request.get('clear'):
            query = Game.query()
            results = query.fetch(1000, keys_only=True)
            while results:
                ndb.delete_multi(results)
                results=query.fetch(1000, keys_only=True)
        reader = csv.DictReader(self.request.get('upload').split('\n'), FIELD_ORDER)
        ndb.Future.wait_all([Game.from_dict(game_data).put_async() for game_data in reader])
        self.add_message('Upload successful', 'success')
        small_process_games.clear_cache()
        player_rankings.clear_cache()
        player_latest.clear_cache()
        self.redirect('/rankings')


class DownloadPage(BaseHandler):
    def get(self):
        self.response.content_type = 'text/csv'
        writer = csv.DictWriter(self.response, FIELD_ORDER)
        writer.writerows(game.to_dict() for game in Game.query().order(Game.date))

application = webapp2.WSGIApplication(
    routes=[
        ('/', FrontPage),
        ('/rankings', RankingPage),
        ('/player/(.+)', PlayerPage),
        ('/upload', UploadPage),
        ('/download', DownloadPage),
    ],
    config={'webapp2_extras.sessions':{'secret_key':'mykey'}},
    debug=True)
