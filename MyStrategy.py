from model.ActionType import ActionType
from model.Building import Building
from model.BuildingType import BuildingType
from model.Bonus import Bonus
from model.BonusType import BonusType
from model.Faction import Faction
from model.Game import Game
from model.LaneType import LaneType
from model.LivingUnit import LivingUnit
from model.Minion import Minion
from model.MinionType import MinionType
from model.Move import Move
from model.Player import Player
from model.PlayerContext import PlayerContext
from model.Projectile import Projectile
from model.ProjectileType import ProjectileType
from model.Unit import Unit
from model.Wizard import Wizard
from model.World import World

import random
import math


class MyStrategy:

    # constants section
    WAYPOINT_RADIUS = 50
    LOW_HP_FACTOR = 0.65
    ENEMY_RANGE = 700
    ALLY_RANGE = 500

    # get modules initialised
    lane = LaneType()
    waypoints = []
    run_away = False
    strategy_steps = 0

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        self.initialize_strategy(game)
        self.initialize_tick(world=world, game=game, me=me)

        # --- add strafe_speed for dodge
        if self.me.life < self.me.max_life * self.LOW_HP_FACTOR:
            self.goto(self.get_previous_waypoint(), move)

        enemies_in_range = self.get_enemies_in_range()
        ally_in_range = self.get_ally_in_range()

        # some information provider section -----------------
        if self.strategy_steps % 100 == 0:
            print('My stats: hp %s of %s, score %s, coords: x %s y %s' % (me.life, me.max_life, me.xp, round(me.x, 2),
                                                                          round(me.y, 2)))
            print('Enemies: minion - %s, wizard - %s, building - %s' %
                  (len(enemies_in_range['minion']), len(enemies_in_range['wizard']), len(enemies_in_range['building'])))
            print('Ally: minion - %s, wizard - %s, building - %s' %
                  (len(ally_in_range['minion']), len(ally_in_range['wizard']), len(ally_in_range['building'])))
            print('Current strategy tick is %s', self.strategy_steps)
            print('')

        # {'minion': ally_minions, 'wizard': ally_wizards, 'building': ally_buildings}

        if ally_in_range['minion'] == 0 and enemies_in_range['minion'] >= 1:
            self.run_away = True
        if (ally_in_range['wizard'] == 0 and ally_in_range['minion'] <= 1) and enemies_in_range['wizard'] > 2:
            self.run_away = True
        if ally_in_range['minion'] == 0 and enemies_in_range['building'] == 1:
            self.run_away = True

        nearest_target = self.get_nearest_target()
        if nearest_target and not self.run_away:
            distance = self.me.get_distance_to(nearest_target.x, nearest_target.y)
            if distance <= self.me.cast_range:
                angle = self.me.get_angle_to(nearest_target.x, nearest_target.y)
                move.turn = angle
                if abs(angle) < game.staff_sector / 2:
                    move.action = ActionType.MAGIC_MISSILE
                    move.cast_angle = angle
                    move.min_cast_distance = distance - nearest_target.radius + game.magic_missile_radius

        self.goto(self.get_next_waypoint(), move)

    # ------ helper functions ---------------------------------------
    def initialize_strategy(self, game):
        random.seed(game.random_seed)
        map_size = game.map_size

        self.waypoints.append([100, map_size - 100])
        self.waypoints.append([150, map_size - 500])
        self.waypoints.append([160, map_size - 600])
        self.waypoints.append([180, map_size - 700])
        self.waypoints.append([200, map_size - 800])
        self.waypoints.append([200, map_size - 900])
        self.waypoints.append([210, map_size * 0.75])
        self.waypoints.append([230, map_size * 0.7])
        self.waypoints.append([240, map_size * 0.67])
        self.waypoints.append([230, map_size * 0.625])
        self.waypoints.append([220, map_size * 0.58])
        self.waypoints.append([215, map_size * 0.55])
        self.waypoints.append([200, map_size * 0.5])
        self.waypoints.append([200, map_size * 0.45])
        self.waypoints.append([200, map_size * 0.4])
        self.waypoints.append([200, map_size * 0.35])
        self.waypoints.append([200, map_size * 0.3])
        self.waypoints.append([200, map_size * 0.25])
        self.waypoints.append([200, 900])
        self.waypoints.append([200, 800])
        self.waypoints.append([200, 700])
        self.waypoints.append([180, 600])
        self.waypoints.append([200, 500])
        self.waypoints.append([220, 400])
        self.waypoints.append([190, 300])
        self.waypoints.append([200, 200])
        self.waypoints.append([300, 210])
        self.waypoints.append([400, 190])
        self.waypoints.append([500, 210])
        self.waypoints.append([600, 190])
        self.waypoints.append([700, 210])
        self.waypoints.append([800, 190])
        self.waypoints.append([900, 210])
        self.waypoints.append([map_size * 0.25, 210])
        self.waypoints.append([map_size * 0.28, 190])
        self.waypoints.append([map_size * 0.31, 210])
        self.waypoints.append([map_size * 0.34, 190])
        self.waypoints.append([map_size * 0.37, 210])
        self.waypoints.append([map_size * 0.4, 190])
        self.waypoints.append([map_size * 0.43, 210])
        self.waypoints.append([map_size * 0.47, 190])
        self.waypoints.append([map_size * 0.53, 210])
        self.waypoints.append([map_size * 0.56, 190])
        self.waypoints.append([map_size * 0.59, 210])
        self.waypoints.append([map_size * 0.62, 190])
        self.waypoints.append([map_size * 0.65, 210])
        self.waypoints.append([map_size * 0.68, 190])
        self.waypoints.append([map_size * 0.71, 210])
        self.waypoints.append([map_size * 0.75, 190])
        self.waypoints.append([map_size - 900, 210])
        self.waypoints.append([map_size - 800, 200])
        self.waypoints.append([map_size - 700, 200])
        self.waypoints.append([map_size - 600, 200])
        self.waypoints.append([map_size - 500, 200])
        self.waypoints.append([map_size - 100, 100])

        self.lane = LaneType.TOP

    def initialize_tick(self, world, game, me):
        self.world = world
        self.game = game
        self.me = me
        self.run_away = False
        self.strategy_steps += 1

    def get_next_waypoint(self):
        last_waypoint_index = len(self.waypoints) - 1
        last_waypoint = self.waypoints[last_waypoint_index]

        for waypoint_index in range(0, last_waypoint_index - 1):
            waypoint = self.waypoints[waypoint_index]

            if self.me.get_distance_to(waypoint[0], waypoint[1]) <= self.WAYPOINT_RADIUS:
                return self.waypoints[waypoint_index + 1]
            if math.hypot(waypoint[0] - last_waypoint[0], waypoint[1] - last_waypoint[1]) < self.me.get_distance_to(
                                                          last_waypoint[0], last_waypoint[1]):
                return waypoint

    def get_previous_waypoint(self):
        first_waypoint = self.waypoints[0]
        for waypoint_index in range(len(self.waypoints) - 1, 0, -1):
            waypoint = self.waypoints[waypoint_index]
            if self.me.get_distance_to(waypoint[0], waypoint[1]) <= self.WAYPOINT_RADIUS:
                return self.waypoints[waypoint_index - 1]
            if math.hypot(waypoint[0] - first_waypoint[0], waypoint[1] - first_waypoint[1]) < self.me.get_distance_to(
                                                           first_waypoint[0], first_waypoint[1]):
                return waypoint

    def goto(self, waypoint, move):
        angle = self.me.get_angle_to(waypoint[0], waypoint[1])
        move.turn = angle
        if abs(angle) < self.game.staff_sector / 4:
            move.speed = self.game.wizard_forward_speed

    def get_nearest_target(self):
        targets = []
        for position in self.world.buildings:
            targets.append(position)
        for position in self.world.wizards:
            targets.append(position)
        for position in self.world.minions:
            targets.append(position)

        nearest_target = None
        nearest_target_distance = 6000
        for target in targets:
            if target.faction == Faction.NEUTRAL or target.faction == self.me.faction:
                continue
            distance = self.me.get_distance_to(target.x, target.y)
            if distance < nearest_target_distance:
                nearest_target = target
                nearest_target_distance = distance
        return nearest_target

    def get_enemies_in_range(self):
        enemy_minions, enemy_wizards, enemy_buildings = [], [], []
        for target in self.world.buildings:
            if target.faction == Faction.NEUTRAL or target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ENEMY_RANGE:
                enemy_buildings.append(target)

        for target in self.world.wizards:
            if target.faction == Faction.NEUTRAL or target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ENEMY_RANGE:
                enemy_wizards.append(target)

        for target in self.world.minions:
            if target.faction == Faction.NEUTRAL or target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ENEMY_RANGE:
                enemy_minions.append(target)
        return {'minion': enemy_minions, 'wizard': enemy_wizards, 'building': enemy_buildings}

    def get_ally_in_range(self):
        ally_minions, ally_wizards, ally_buildings = [], [], []
        for target in self.world.buildings:
            if target.faction == self.me.faction and self.me.get_distance_to(target.x, target.y) <= self.ALLY_RANGE:
                ally_buildings.append(target)

        for target in self.world.wizards:
            if target.faction == self.me.faction and self.me.get_distance_to(target.x, target.y) <= self.ALLY_RANGE:
                ally_wizards.append(target)

        for target in self.world.minions:
            if target.faction == self.me.faction and self.me.get_distance_to(target.x, target.y) <= self.ALLY_RANGE:
                ally_minions.append(target)
        return {'minion': ally_minions, 'wizard': ally_wizards, 'building': ally_buildings}


