#!/usr/bin/env python 

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import math

K=50

Base = declarative_base()

class Player(Base):
	__tablename__ = 'players'
	name=Column(String, primary_key=True)
	wins_front = relationship("Game", backref="winner_front")

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return "<Player('%s')>" % self.name

class Rating(Base):
	__tablename__ = 'ratings'
	id=Column(Integer, primary_key=True)
	rating = Column(Integer)
	player_name = Column(String, ForeignKey('players.name'))
	after_game_id = Column(Integer, ForeignKey('games.id'))

	player = relationship("Player")
	after_game = relationship("Game")

	def __init__(self, player, rating, after_game):
		self.player_name = player
		self.rating=rating
		self.after_game_id=after_game

	def __repr__(self):
		return "<Rating('%s','%d','%s')>" % (self.player, self.rating, self.after_game)

class Game(Base):
	__tablename__ = 'games'
	id=Column(Integer, primary_key=True)
	winner_front_name = Column(String, ForeignKey('players.name'))
	winner_back_name = Column(String, ForeignKey('players.name'))
	loser_front_name = Column(String, ForeignKey('players.name'))
	loser_back_name = Column(String, ForeignKey('players.name'))
	winner_points = Column(Integer)
	loser_points = Column(Integer)

	#winner_front = relationship("Player")
	winner_back = relationship("Player")
	loser_front = relationship("Player")
	loser_back = relationship("Player")

	def __init__(self, winner_front, winner_back, loser_front, loser_back, winner_ponts, loser_ponts):
		self.winner_front_name = winner_front
		self.winner_back_name = winner_back
		self.loser_front_name = loser_front
		self.loser_back_name = loser_back
		self.winner_points = winner_points
		self.loser_points = loser_points

	def __repr__(self):
		return "<Game('%s','%s','%s','%s','%d','%d')>" % (self.winner_front_name, self.winner_back_name, self.loser_front_name, self.loser_back_name, self.winner_points, self.loser_points)

	def adjustment_points(self):
		D = loser_front.rating + loser_back.rating - winner_front.rating - winner_back.rating
		E = 1.0 / (1+math.pow(10,D/800.0))
		return int(round(K*(float(self.winner_points)/self.loser_points-E)))
		

if __name__ == '__main__':
	engine = create_engine('sqlite:///:memory:', echo=True)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	session = Session()

	for player in open('players'):
		player=player.strip()
		player,rating = player.split("\t")
		session.add(Player(player))
		session.add(Rating(player, None))
	session.commit()

	for game in open('games'):
		game = game.strip()
		winner_front, winner_back, loser_front, loser_back, winner_points, loser_points = game.split("\t")
		session.add(Game(winner_front, winner_back, loser_front, loser_back, winner_points, loser_points))
		D = players[loser1] + players[loser2] - players[winner1] - players[winner2]
		E = 1.0 / (1+math.pow(10,D/800.0))
		points = K*(1.0-E)
		points = int(round(points))
		players[winner1] += points
		players[winner2] += points
		players[loser1] -= points
		players[loser2] -= points
	session.commit()
