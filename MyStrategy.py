from model.ActionType import ActionType
from model.Faction import Faction
from model.Game import Game
from model.LaneType import LaneType
from model.Move import Move
from model.ProjectileType import ProjectileType
from model.Wizard import Wizard
from model.World import World

import random
import math


class IndirectedGraph:

    def __init__(self):
        self.__adjacent = {}
        self.__vertex_count = 0
        self.__edges_count = 0

    def add_connection(self, source, destination):
        if source in self.__adjacent:
            self.__adjacent[source].append(destination)
        else:
            self.__adjacent[source] = [destination]
            self.__vertex_count += 1

        if destination in self.__adjacent:
            self.__adjacent[destination].append(source)
        else:
            self.__adjacent[destination] = [source]
            self.__vertex_count += 1
        self.__edges_count += 1

    def adjacent_nodes(self, source):
        return set(self.__adjacent[source])

    def vertex_count(self):
        return self.__vertex_count

    def edges_count(self):
        return self.__edges_count

    def vertex_degree(self, source):
        if source in self.__adjacent:
            return len(self.__adjacent[source])
        else:
            return None

    def vertexes(self):
        return self.__adjacent.keys()


class MyStrategy:
    # initials
    me = None
    world = None
    game = None
    move_ = None

    # constants section
    WAYPOINT_RADIUS = 250
    LOW_HP_FACTOR = [0.6, 0.75]
    ATTACK_RANGE = 500
    ALLY_RANGE = 600
    LOW_HP_ENEMY_SWITCH = 12 * 3   # 12 - wizard_damage
    PATH_FINDING_GRID = 35 * 10    # 35 - wizard_radius
    PATH_FINDING_CELL_RADIUS = 25  # x2
    MAX_SPEED = 4
    # stay in range of attack
    ENEMY_CLOSE_RANGE = 400
    ENEMY_IN_RANGE_TICK = 0        # 50
    BACK_ZONE = 150
    BACK_DISTANCE = 100
    # catch me
    EVADE_DISTANCE = 500
    # stuck defence
    NO_MOVE = 0
    PREVIOUS_POS = None
    MAX_NO_MOVE = 10

    # bonus
    BONUS_POINT_TOP = [1200, 1200]
    BONUS_POINT_BOT = [2800, 2800]
    CREATE_TICK = 2500

    # get modules initialised
    lane = LaneType()
    waypoints = []
    strategy_steps = 0
    start_positions = []
    respawn = []

    def move(self, me: Wizard, world: World, game: Game, move: Move):

        if self.strategy_steps == 0:
            self.initialize_strategy(game, me)
        self.initialize_tick(world=world, game=game, me=me, move=move)

        # some information provider section -----------------
        enemies_in_range = self.get_enemies_in_attack_range()
        ally_in_range = self.get_ally_in_shared_exp_range()
        if self.strategy_steps % 50 == 0:
            print('My stats: hp %s of %s, score %s, coords: x %s y %s' % (me.life, me.max_life, me.xp, round(me.x, 2),
                                                                          round(me.y, 2)))
            print('Enemies: minion - %s, wizard - %s, building - %s' %
                  (len(enemies_in_range['minion']), len(enemies_in_range['wizard']), len(enemies_in_range['building'])))
            print('Ally: minion - %s, wizard - %s, building - %s' %
                  (len(ally_in_range['minion']), len(ally_in_range['wizard']), len(ally_in_range['building'])))
            print('Current strategy tick is %s' % self.strategy_steps)
            print('')

        # go back at the beginning for not being stuck with the others
        if self.strategy_steps == 1:
            angle = 0
            if self.respawn == self.start_positions[2]:
                print('Start position #%s %s' % (2, self.respawn))
                angle = self.me.get_angle_to(self.me.x - self.BACK_DISTANCE, self.me.y + self.BACK_DISTANCE)
            self.move_.turn = angle
            self.move_.speed = self.game.wizard_backward_speed
            return None
        else:
            if self.strategy_steps < 40:
                angle = 0
                if self.respawn == self.start_positions[2]:
                    angle = self.me.get_angle_to(100, 3800)
                self.move_.turn = angle
                self.move_.speed = self.game.wizard_backward_speed
                return None

        # in game-check, if stuck
        if self.me.x == self.PREVIOUS_POS[0] and self.me.y == self.PREVIOUS_POS[1]:
            self.NO_MOVE += 1
            if self.NO_MOVE >= self.MAX_NO_MOVE:
                move.action = ActionType.MAGIC_MISSILE
                move.cast_angle = self.me.angle
                self.move_.turn = self.game.wizard_max_turn_angle
                self.move_.speed = self.game.wizard_forward_speed
                self.move_.strafe_speed = self.game.wizard_strafe_speed
                return None
        self.PREVIOUS_POS = [self.me.x, self.me.y]

        # low hp run back
        if self.me.life < self.me.max_life * self.LOW_HP_FACTOR[0]:
            if self.me.life < self.me.max_life * self.LOW_HP_FACTOR[1]:
                print('go back - low hp: x: %s y: % s' % (round(self.me.x, 1), round(self.me.y, 1)))
                self.goto(self.get_previous_waypoint())
            return None

        # bonus collection
        # if self.lane == LaneType.TOP:
        #     if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) < 700:
        #         if self.world.bonuses[0]:
        #             angle = self.me.get_angle_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1])
        #             self.move_.turn = angle
        #             self.move_.speed = self.game.wizard_forward_speed
        # if self.lane == LaneType.BOTTOM:
        #     if self.me.get_distance_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1]) < 700:
        #         if self.world.bonuses[0]:
        #             angle = self.me.get_angle_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1])
        #             self.move_.turn = angle
        #             self.move_.speed = self.game.wizard_forward_speed

        # staying close to frontier
        if self.ENEMY_IN_RANGE_TICK > 0:
            if self.me.x < 70:
                angle = self.me.get_angle_to(self.me.x, self.me.y + self.BACK_DISTANCE)
                self.move_.turn = angle
                self.move_.speed = self.game.wizard_backward_speed
            elif self.me.y < 70:
                angle = self.me.get_angle_to(self.me.x, self.me.y + self.BACK_DISTANCE)
                self.move_.turn = angle
                self.move_.speed = self.game.wizard_backward_speed
            else:
                self.move_.speed = -self.game.wizard_backward_speed
            self.ENEMY_IN_RANGE_TICK -= 1

            # switch to close enemy
            nearest_enemy_wizard = self.get_closest_or_with_low_hp_enemy_wizard_in_attack_range()
            if nearest_enemy_wizard is not None:
                my_target = nearest_enemy_wizard
            else:
                my_target = self.get_nearest_target_in_my_visible_range()

            if my_target:
                distance = self.me.get_distance_to(my_target.x, my_target.y)
                if distance <= self.me.cast_range:
                    angle = self.me.get_angle_to(my_target.x, my_target.y)
                    move.turn = angle
                    if abs(angle) < game.staff_sector / 2:
                        if self.me.remaining_cooldown_ticks_by_action[2] == 0:
                            print('RANGE_MAGIC_MISSILE fires to %s' % [my_target.x, my_target.y])
                            move.action = ActionType.MAGIC_MISSILE
                            move.cast_angle = angle
                            move.min_cast_distance = distance - my_target.radius + game.magic_missile_radius
            return None

        # set a flag if too close to the enemies
        the_closest = self.get_closest_enemy()
        # TODO add obstacles check
        if the_closest is not None:
            if self.me.life == self.me.max_life:
                self.ENEMY_IN_RANGE_TICK = 1
            else:
                self.ENEMY_IN_RANGE_TICK = 40
            print('range limit active, me x: %s, y: %s, HP - %s' % (round(self.me.x, 1), round(self.me.y, 1),
                                                                    self.me.life))
            delta_x = self.me.x - the_closest.x
            delta_y = self.me.y - the_closest.y
            angle = None

            # I
            if delta_y > 0 and abs(delta_x) <= self.BACK_ZONE:
                if self.me.y > 3800:
                    angle = self.me.get_angle_to(self.me.x, 3900)
                else:
                    angle = self.me.get_angle_to(self.me.x, self.me.y + self.BACK_DISTANCE)
            # II
            elif delta_x < 0 and abs(delta_y) <= self.BACK_ZONE:
                if self.me.x <= 200:
                    angle = self.me.get_angle_to(self.me.x, self.me.y - self.BACK_DISTANCE * 2)
                else:
                    angle = self.me.get_angle_to(self.me.x - self.BACK_DISTANCE, self.me.y)

            if angle is None:
                self.move_.turn = -self.me.angle
            else:
                self.move_.turn = -angle

            self.move_.speed = -self.game.wizard_backward_speed

            if self.me.remaining_cooldown_ticks_by_action[2] == 0 and the_closest is not None:
                angle_fire = self.me.get_angle_to(the_closest.x, the_closest.y)
                if abs(angle_fire) < game.staff_sector / 2:
                    print('Range_MAGIC_MISSILE fires to %s' % [the_closest.x, the_closest.y])
                    move.action = ActionType.MAGIC_MISSILE
                    move.cast_angle = self.me.get_angle_to(the_closest.x, the_closest.y)
                    move.min_cast_distance = self.me.get_distance_to(the_closest.x, the_closest.y) - \
                                             the_closest.radius + self.game.magic_missile_radius
            return None

        # if on the edge of range and nothing triggers
        nearest_enemy_wizard = self.get_closest_or_with_low_hp_enemy_wizard_in_attack_range()
        if nearest_enemy_wizard:
            my_target = nearest_enemy_wizard
        else:
            my_target = self.get_nearest_target_in_my_visible_range()

        # attack something in range
        if my_target:
            distance = self.me.get_distance_to(my_target.x, my_target.y)
            if self.strategy_steps % 10:
                print('Targets in range: %s, closest @%s' % (len(enemies_in_range['minion']) +
                                                             len(enemies_in_range['wizard']) +
                                                             len(enemies_in_range['building']), round(distance, 1)))
            if distance <= self.me.cast_range:
                angle = self.me.get_angle_to(my_target.x, my_target.y)
                move.turn = angle
                if abs(angle) < game.staff_sector / 2:
                    # self.me.remaining_action_cooldown_ticks == 0
                    # remaining_cooldown_ticks_by_action[2] magic_missile - 60 ticks
                    if self.me.remaining_cooldown_ticks_by_action[2] == 0:
                        print('MAGIC_MISSILE fires to %s' % [my_target.x, my_target.y])
                        move.action = ActionType.MAGIC_MISSILE
                        move.cast_angle = angle
                        move.min_cast_distance = distance - my_target.radius + game.magic_missile_radius

        # nothing to do - go further
        self.goto(self.get_next_waypoint())

    def initialize_strategy(self, game, me):
        random.seed(game.random_seed)
        map_size = game.map_size

        self.respawn = [me.x, me.y]
        self.PREVIOUS_POS = self.respawn

        self.start_positions.append([100, 3700])
        self.start_positions.append([300, 3900])
        self.start_positions.append([200, 3800])
        self.start_positions.append([300, 3800])
        self.start_positions.append([200, 3700])

        if self.respawn == self.start_positions[0] or self.respawn == self.start_positions[4]:
            self.waypoints.append([50, map_size - 50])
            self.waypoints.append([200, map_size * 0.75])
            self.waypoints.append([200, map_size * 0.5])
            self.waypoints.append([200, map_size * 0.3])
            self.waypoints.append([250, 250])
            self.waypoints.append([map_size * 0.25, 200])
            self.waypoints.append([map_size * 0.5, 200])
            self.waypoints.append([map_size * 0.75, 200])
            self.waypoints.append([map_size - 200, 200])
            self.lane = LaneType.TOP
        elif self.respawn == self.start_positions[1] or self.respawn == self.start_positions[3]:
            self.waypoints.append([50, map_size - 50])
            self.waypoints.append([map_size * 0.3, map_size - 250])
            self.waypoints.append([map_size * 0.5, map_size - 250])
            self.waypoints.append([map_size * 0.8, map_size - 250])
            self.waypoints.append([map_size - 250, map_size - 250])
            self.waypoints.append([map_size - 200, map_size * 0.75])
            self.waypoints.append([map_size - 200, map_size * 0.5])
            self.waypoints.append([map_size - 200, map_size * 0.25])
            self.waypoints.append([map_size - 200, 200])
            self.lane = LaneType.BOTTOM
        elif self.respawn == self.start_positions[2]:
            self.waypoints.append([50, map_size - 50])
            self.waypoints.append([200, map_size * 0.75])
            self.waypoints.append([200, map_size * 0.5])
            self.waypoints.append([200, map_size * 0.3])
            self.waypoints.append([250, 250])
            self.waypoints.append([map_size * 0.25, 200])
            self.waypoints.append([map_size * 0.5, 200])
            self.waypoints.append([map_size * 0.75, 200])
            self.waypoints.append([map_size - 200, 200])
            self.lane = LaneType.TOP

    def initialize_tick(self, world, game, me, move):
        self.world = world
        self.game = game
        self.me = me
        self.move_ = move
        self.strategy_steps += 1
        if self.strategy_steps >= 1000:
            self.MAX_SPEED = self.game.wizard_forward_speed

    def get_enemies_in_attack_range(self):
        enemy_minions, enemy_wizards, enemy_buildings = [], [], []
        for target in self.world.buildings:
            if target.faction == Faction.NEUTRAL or target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ATTACK_RANGE:
                enemy_buildings.append(target)

        for target in self.world.wizards:
            if target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ATTACK_RANGE:
                enemy_wizards.append(target)

        for target in self.world.minions:
            if target.faction == Faction.NEUTRAL or target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ATTACK_RANGE:
                enemy_minions.append(target)
        return {'minion': enemy_minions, 'wizard': enemy_wizards, 'building': enemy_buildings}

    def get_ally_in_shared_exp_range(self):
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

    def goto(self, waypoint):
        if self.strategy_steps % 10 == 0:
            print('Milestone %s' % waypoint)

        waypoint_bfs = self.path_finder(waypoint)

        if self.strategy_steps % 10 == 0:
            print(waypoint, waypoint_bfs)
        if waypoint_bfs:
            angle = self.me.get_angle_to(waypoint_bfs[0], waypoint_bfs[1])
            self.move_.turn = angle
            self.move_.speed = self.MAX_SPEED
        else:
            if waypoint:
                angle = self.me.get_angle_to(waypoint[0], waypoint[1])
                self.move_.turn = angle
                self.move_.speed = self.MAX_SPEED
            # else:
            #     distance = 6000
            #     best_index = -1
            #     for index in range(0, len(self.waypoints)):
            #         if self.me.get_distance_to(self.waypoints[index][0], self.waypoints[index][1]) < distance:
            #             distance = self.me.get_distance_to(self.waypoints[index][0], self.waypoints[index][1])
            #             best_index = index
            #     angle = self.me.get_angle_to(self.waypoints[best_index][0], self.waypoints[best_index][1])
            #     self.move_.turn = angle
            #     self.move_.speed = self.game.wizard_forward_speed

    def get_closest_or_with_low_hp_enemy_wizard_in_attack_range(self):
        enemy_wizards = []
        for target in self.world.wizards:
            if target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ATTACK_RANGE:
                enemy_wizards.append(target)
        if len(enemy_wizards) > 0:
            the_closest_enemy_wizard = enemy_wizards[0]
            for enemy in enemy_wizards:
                if self.me.get_distance_to(enemy.x, enemy.y) <= self.me.get_distance_to(the_closest_enemy_wizard.x,
                                                                                        the_closest_enemy_wizard.y):
                    the_closest_enemy_wizard = enemy
            for enemy in enemy_wizards:
                if enemy.life < self.LOW_HP_ENEMY_SWITCH and self.me.get_distance_to(enemy.x, enemy.y) < \
                        self.game.wizard_cast_range:
                    return enemy
            return the_closest_enemy_wizard
        else:
            return None

    def get_nearest_target_in_my_visible_range(self):
        targets = []
        for position in self.world.buildings:
            targets.append(position)
        for position in self.world.wizards:
            targets.append(position)
        for position in self.world.minions:
            targets.append(position)

        nearest_target = None
        nearest_target_distance = 700
        for target in targets:
            if target.faction == Faction.NEUTRAL or target.faction == self.me.faction:
                continue
            distance = self.me.get_distance_to(target.x, target.y)
            if distance < nearest_target_distance:
                nearest_target = target
                nearest_target_distance = distance
        return nearest_target

    def get_closest_enemy(self):
        targets = []
        for position in self.world.buildings:
            if self.me.get_distance_to(position.x, position.y) <= self.ENEMY_CLOSE_RANGE:
                if position.faction == self.me.faction or position.faction == Faction.NEUTRAL:
                    continue
                else:
                    targets.append(position)
        for position in self.world.wizards:
            if self.me.get_distance_to(position.x, position.y) <= self.ENEMY_CLOSE_RANGE:
                if position.faction == self.me.faction or position.faction == Faction.NEUTRAL:
                    continue
                else:
                    targets.append(position)
                targets.append(position)
        for position in self.world.minions:
            if self.me.get_distance_to(position.x, position.y) <= self.ENEMY_CLOSE_RANGE:
                if position.faction == self.me.faction or position.faction == Faction.NEUTRAL:
                    continue
                else:
                    targets.append(position)
                targets.append(position)

        if targets:
            result = targets[0]
            for target in targets:
                if self.me.get_distance_to(result.x, result.y) > self.me.get_distance_to(target.x, target.y):
                    result = target
            return result
        return None

    # ------ heuristics functions ---------------------------------------
    # points table:
    # only HOST:
    #   damage dealt / 0.25 = points  attacks with the same spell = 60 ticks, diff. actions 30 ticks
    #   bonus obtain = 200 points
    # everybody in range 600:  + 67% bonus if more than 1 ally // amount of ally
    #   25 % of tower or minion max_life:
    #       orc = 25  points /  20 points
    #       fet = 25  points /  20 points
    #       tow = 250 points /  208 points
    #   100 % max_life of enemy wiz. = 100 points
    # winner = 1000 points
    #

    def path_finder(self, waypoint):
        # wizard_radius         # 35
        # faction_base_radius   # 100
        # minion_radius         # 25
        # guardian_tower_radius # 50
        # tree radius           # 20 - 50
        #
        # wizard_strafe_speed   # 3.0
        # wizard_backward_speed # 3.0
        # wizard_forward_speed  # 4.0
        # wizard_vision_range   # 600.0 distance between waypoint ~ 600.0

        start = [self.me.x, self.me.y]           # x:200 y:1000
        if waypoint:
            finish = [waypoint[0], waypoint[1]]      # x:200 y:600
        else:
            finish = self.waypoints[1]
        # start = [200, 1000]
        # finish = [200, 600]
        graph = IndirectedGraph()

        lb = [start[0] - self.PATH_FINDING_GRID, start[1] + self.PATH_FINDING_GRID]    # lb: x: -100 y: 1300
        rb = [start[0] + self.PATH_FINDING_GRID, start[1] + self.PATH_FINDING_GRID]    # rb: x: 500 y: 1300
        lt = [finish[0] - self.PATH_FINDING_GRID, finish[1] - self.PATH_FINDING_GRID]  # lt: x: -100 y: 300
        rt = [finish[0] + self.PATH_FINDING_GRID, finish[1] - self.PATH_FINDING_GRID]  # lt: x: 500 y: 300

        # filter if in map_size
        if lb[0] <= 0:
            lb[0] = 1
        if lb[1] >= self.game.map_size:
            lb[1] = self.game.map_size - 1
        if rb[0] >= self.game.map_size:
            rb[0] = self.game.map_size - 1
        if rb[1] >= self.game.map_size:
            rb[1] = self.game.map_size - 1
        if lt[0] <= 0:
            lt[0] = 1
        if lt[1] <= 0:
            lt[1] = 1
        if rt[0] >= self.game.map_size:
            rt[0] = self.game.map_size - 1
        if rt[1] <= 0:
            rt[1] = 1

        step = self.PATH_FINDING_CELL_RADIUS
        net_2d = []

        for net_y in range(int(min(lt[1], rt[1]) + step), int(max(lb[1], rb[1]) - step), int(step * 2)):
            line_x = []
            for net_x in range(int(min(lb[0], lt[0]) + step), int(max(rb[0], rt[0]) - step), int(step * 2)):
                line_x.append([net_x, net_y])
            net_2d.append(line_x)

        # get obstacles
        obstacles = self.get_obstacles_in_zone([
            int(min(lb[0], lt[0]) + step), int(max(rb[0], rt[0]) - step),
            int(min(lt[1], rt[1]) + step), int(max(lb[1], rb[1]) - step)])

        # for obstacle in obstacles:
        #     if obstacle.faction == self.me.faction:
        #         print(obstacle.x, obstacle.y)
        # print('')

        # generate grid cell names
        net_2d_name = []
        for line_v in range(0, len(net_2d)):
            net_2d_v = []
            for line_h in range(0, len(net_2d[line_v])):
                net_2d_v.append((line_v + 1) * 100 + line_h)
            net_2d_name.append(net_2d_v)

        # # make connections between elements
        # for line_v in range(0, len(net_2d)):
        #     for line_h in range(0, len(net_2d[line_v]) - 1):
        #         graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v][line_h + 1])
        #
        # for line_v in range(0, len(net_2d) - 1):
        #     for line_h in range(0, len(net_2d[line_v])):
        #         graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v + 1][line_h])
        #
        # for line_v in range(0, len(net_2d) - 1):
        #     for line_h in range(0, len(net_2d[line_v]) - 1):
        #         graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v + 1][line_h + 1])
        #
        # for line_v in range(len(net_2d) - 1, 1, -1):
        #     for line_h in range(len(net_2d[line_v]) - 1, 1, -1):
        #         graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v - 1][line_h - 1])

        # make connections between elements
        for line_v in range(0, len(net_2d)):
            for line_h in range(0, len(net_2d[line_v]) - 1):
                if not self.is_obstacle_in_node(net_2d[line_v][line_h + 1], obstacles, cell_radius=int(step)):
                    graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v][line_h + 1])
                # else:
                #     print('Excluded node %s #%s' % (net_2d[line_v][line_h + 1], (line_v + 1) * 100 + line_h))

        for line_v in range(0, len(net_2d) - 1):
            for line_h in range(0, len(net_2d[line_v])):
                if not self.is_obstacle_in_node(net_2d[line_v + 1][line_h], obstacles, cell_radius=int(step)):
                    graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v + 1][line_h])
                # else:
                #     print('Excluded node %s #%s' % (net_2d[line_v + 1][line_h], (line_v + 1) * 100 + line_h))

        for line_v in range(0, len(net_2d) - 1):
            for line_h in range(0, len(net_2d[line_v]) - 1):
                if not self.is_obstacle_in_node(net_2d[line_v + 1][line_h + 1], obstacles, cell_radius=int(step)):
                    graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v + 1][line_h + 1])
                # else:
                #     print('Excluded node %s #%s' % (net_2d[line_v + 1][line_h + 1], (line_v + 1) * 100 + line_h))

        for line_v in range(len(net_2d) - 1, 1, -1):
            for line_h in range(len(net_2d[line_v]) - 1, 1, -1):
                if not self.is_obstacle_in_node(net_2d[line_v - 1][line_h - 1], obstacles, cell_radius=int(step)):
                    graph.add_connection(net_2d_name[line_v][line_h], net_2d_name[line_v - 1][line_h - 1])
                # else:
                #     print('Excluded node %s #%s' % (net_2d[line_v - 1][line_h - 1], (line_v + 1) * 100 + line_h))

        # convert start and finish nodes
        start_node = self.return_node(net_2d, [self.me.x, self.me.y], int(step))
        end_node = self.return_node(net_2d, waypoint, int(step))

        if start_node is None:
            print('no start waypoint found')
            return waypoint

        if end_node is None:
            print('no finish waypoint found')
            return waypoint

        # v_name = (int(start_node) // 100) - 1
        # h_name = int(start_node) % 100
        # next_coords = net_2d[v_name][h_name]
        #
        # v_name = (int(end_node) // 100) - 1
        # h_name = int(end_node) % 100
        # next_coords = net_2d[v_name][h_name]

        next_path = self.bfs(graph_to_search=graph, start=start_node, end=end_node)
        del graph

        # return coordinates based on square name
        if next_path:
            if len(next_path) > 1:
                next_node = next_path[1]
                v_name = (int(next_node) // 100) - 1
                h_name = int(next_node) % 100
                next_coords = net_2d[v_name][h_name]
                return next_coords
            else:
                return waypoint

    @staticmethod
    def bfs(graph_to_search, start, end):
        queue = [[start]]
        visited = set()
        while queue:
            path = queue.pop(0)
            vertex = path[-1]
            if vertex == end:
                return path
            elif vertex not in visited:
                for current_neighbour in graph_to_search.adjacent_nodes(vertex):
                    new_path = list(path)
                    new_path.append(current_neighbour)
                    queue.append(new_path)
                    if current_neighbour == end:
                        return new_path
                visited.add(vertex)

    @staticmethod
    def is_obstacle_in_node(target_cell, obstacles, cell_radius):
        for obstacle in obstacles:
            squared_dist = (target_cell[0] - obstacle.x) ** 2 + (target_cell[1] - obstacle.y) ** 2
            if squared_dist <= cell_radius ** 2:
                return True
        return False

    @staticmethod
    def return_node(net, coords, cell_radius):
        if coords:
            for v_line in range(0, len(net)):
                for h_line in range(0, len(net[0])):
                    if (coords[0] >= net[v_line][h_line][0] - cell_radius) and (coords[0] <= net[v_line][h_line][0] + cell_radius) \
                            and (coords[1] >= net[v_line][h_line][1] - cell_radius) and (coords[1] <= net[v_line][h_line][1] + cell_radius):
                        return (v_line + 1) * 100 + h_line
        return None

    def get_obstacles_in_zone(self, range_xy):
        obstacles, objects = [], []

        for target in self.world.buildings:
            objects.append(target)
        for target in self.world.wizards:
            objects.append(target)
        for target in self.world.minions:
            objects.append(target)
        for target in self.world.trees:
            objects.append(target)

        for target in objects:
            if (target.x > range_xy[0]) and (target.x < range_xy[1]):
                if (target.y > range_xy[2]) and (target.y < range_xy[3]):
                    if target.x != self.me.x:
                        obstacles.append(target)
        return obstacles

    def dodge_and_evade(self):
        # projectile parameters:
        #  - dodge:
        #       orc: range 50
        #  - evade:
        #       magic_missile: r 10, spd 40, dmg 12
        #       frostbolt    : r 15, spd 35, dmg 35
        #       fireball     : r 20, spd 30, dmg 24 / 240 ticks + r100 dmg 12 linear
        #       dart         : r 5,  spd 50, dmg 6
        #

        projectiles = []
        for projectile in self.world.projectiles:
            if self.me.get_distance_to(projectile.x, projectile.y) < self.EVADE_DISTANCE:
                if projectile.faction == self.me.faction:
                    continue
                else:
                    projectiles.append(projectile)
        if len(projectiles) > 0:
            print('Number of projectiles in attack range: %s' % len(projectiles))

            # target is me?
            tick_explode = 0
            for projectile in projectiles:
                distance_to_me = self.me.get_distance_to(projectile.x, projectile.y)
                distance_to_me = distance_to_me - self.me.radius - projectile.radius
                if projectile.type == ProjectileType.MAGIC_MISSILE:
                    tick_explode = distance_to_me / 40
                elif projectile.type == ProjectileType.FIREBALL:
                    tick_explode = distance_to_me / 30
                elif projectile.type == ProjectileType.FROST_BOLT:
                    tick_explode = distance_to_me / 35
                elif projectile.type == ProjectileType.DART:
                    tick_explode = distance_to_me / 50
                dodge_time = tick_explode * self.game.wizard_strafe_speed
                print(dodge_time)




        return False

