from model.ActionType import ActionType
from model.Faction import Faction
from model.Game import Game
from model.LaneType import LaneType
from model.MinionType import MinionType
from model.Move import Move
from model.ProjectileType import ProjectileType
from model.Status import Status
from model.StatusType import StatusType
from model.Wizard import Wizard
from model.World import World

import random
import math
import time

# debug = False
try:
    from debug_client import DebugClient
except:
    debug = None
else:
    debug = DebugClient()


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
    # WAYPOINT_RADIUS = 250
    LOW_HP_FACTOR = [0.7, 0.72]
    ATTACK_RANGE = 500
    ALLY_RANGE = 600
    LOW_HP_ENEMY_SWITCH = 12 * 2                # 12 - wizard_damage
    PATH_FINDING_GRID = 35 * 6                  # 35 - wizard_radius
    PATH_FINDING_CELL_RADIUS = 35               # x2

    # stay in range of attack
    ENEMY_CLOSE_RANGE = 400
    ENEMY_IN_RANGE_TICK = 0                     # 50
    BACK_ZONE = 150
    BACK_DISTANCE = 100
    # catch me
    EVADE_DISTANCE = 500
    MOVE_LOW_HP = 0
    MINION_STAY = [1360, 6]                     # check it
    ENEMIES_RANGE_LIMIT = [475, 450, 350, 270]  # wizard, building, fetish, orc TODO make it based on ATTACK RANGE value
    RANGE_LIMIT_ACTIVE = False
    # stuck defence
    NO_MOVE = 0
    PREVIOUS_POS = None
    MAX_NO_MOVE = 15
    FIGHTING = False
    # new waypoint system
    CURRENT_WAYPOINT_INDEX = 1
    LAST_WAYPOINT_INDEX = 0
    WAIT_WAYPOINT_INDEX = 6
    MOVE_FORWARD = True
    WAYPOINT_RADIUS_NEW = 70
    WAS_DEAD = True
    DEATH_COUNT = 0

    # bonus
    BONUS_POINT_TOP = [1200, 1200]
    BONUS_POINT_BOT = [2800, 2800]
    CREATE_BONUS_TICK = 2500
    BONUS_EXIST = False
    BONUS_COUNT = 0
    BONUS_GO = False

    # get modules initialised
    lane = LaneType()
    waypoints_top, waypoints_mid, waypoints_bot = [], [], []
    waypoints = []
    bonus_waypoints = []
    cross_the_map_waypoint = []
    strategy_steps = 0
    start_positions = []
    respawn = []

    # optimization section
    bot_time = 0
    strategy_time = 0
    graph_profile = 0
    bfs_profile = 0
    units_profile = 0

    # debug parameters
    debug_next_milestone = [400, 3600]
    debug_next_waypoint = [400, 3600]
    debug_view_path = []
    debug_obstacles = []

    # game analisys parameters
    MIN_PUSH_AMOUNT = 1

    def visual_debugger(self):
        with debug.post() as dbg:
            dbg.text(self.me.x, self.me.y - 35, 'x: %s, y: %s' % (round(self.me.x), round(self.me.y)), (0, 0, 0))
            dbg.line(self.me.x, self.me.y, self.debug_next_milestone[0], self.debug_next_milestone[1], (0, 0, 0))
            dbg.line(self.me.x, self.me.y, self.debug_next_waypoint[0], self.debug_next_waypoint[1], (0, 0.5, 1))

            if len(self.debug_view_path) > 2:
                for i in range(2, len(self.debug_view_path)):
                    dbg.line(self.debug_view_path[i-1][0], self.debug_view_path[i-1][1],
                             self.debug_view_path[i][0], self.debug_view_path[i][1], (0.5, 0.5, 0.5))

            if len(self.debug_obstacles) > 0:
                for target in self.debug_obstacles:
                    dbg.circle(target.x, target.y, target.radius, (0, 0, 0))

    def move(self, me: Wizard, world: World, game: Game, move: Move):

        start_strategy_execute = time.time()

        # initialize
        if self.strategy_steps == 0:
            self.initialize_strategy(game, me)
        self.initialize_tick(world=world, game=game, me=me, move=move)

        # choose TOP or BOT
        if self.strategy_steps < 300:
            return None
        else:
            if self.strategy_steps == 300:
                self.lane = self.get_a_line_to_push()

                if self.lane == LaneType.TOP:
                    self.waypoints = self.waypoints_top
                if self.lane == LaneType.BOTTOM:
                    self.waypoints = self.waypoints_bot
                if self.lane == LaneType.MIDDLE:
                    self.waypoints = self.waypoints_mid
                print('Lane is %s' % self.lane)

        # get all tick information:
        units_timer = time.time()

        enemies_in_range = self.get_enemies_in_attack_range()
        enemies = enemies_in_range
        wizard, building, fetish, orc = self.get_the_closest_of_attack_range(enemies_in_range)
        ally_in_range = self.get_ally_in_shared_exp_range()

        nearest_enemy_wizard = self.get_closest_or_with_low_hp_enemy_wizard_in_attack_range()
        tower = self.get_tower_in_range()
        if nearest_enemy_wizard:
            my_target = nearest_enemy_wizard
        elif tower:
            my_target = tower
        else:
            my_target = self.get_nearest_target_in_my_visible_range()

        self.units_profile += time.time() - units_timer

        # visual debugger activation with information from a tick ago
        if debug:
            self.visual_debugger()

        # some information provider section
        if self.strategy_steps % 100 == 0:
            print('My stats: hp %s of %s, score %s, coords: x %s y %s' % (me.life, me.max_life, me.xp, round(me.x, 2),
                                                                          round(me.y, 2)))
            print('Enemies: minion - %s, wizard - %s, building - %s' %
                  (len(enemies_in_range['minion']), len(enemies_in_range['wizard']), len(enemies_in_range['building'])))
            print('Ally: minion - %s, wizard - %s, building - %s' %
                  (len(ally_in_range['minion']), len(ally_in_range['wizard']), len(ally_in_range['building'])))
            print('Current strategy tick is %s, Time spent: %s' % (self.strategy_steps,
                                                                   round(time.time() - self.bot_time, 2)))
            print('Time bot: %s s, units profiler: %s, graph: %s, BFS: %s' % (round(self.strategy_time, 2),
                  round(self.units_profile, 2), round(self.graph_profile, 2), round(self.bfs_profile, 2)))
            print('Death counter: %s Bonus counter: %s' % (self.DEATH_COUNT, self.BONUS_COUNT))
            print('----------------')

        # go back at the beginning for not being stuck with the others
        if self.strategy_steps == 1:
            angle = 0
            if self.respawn == self.start_positions[2]:
                print('Start position #%s %s' % (2, self.respawn))
                angle = self.me.get_angle_to(self.me.x - self.BACK_DISTANCE, self.me.y + self.BACK_DISTANCE)
                self.MINION_STAY = [1460, 6]
            self.move_.turn = angle
            self.move_.speed = self.game.wizard_backward_speed

            self.strategy_time += time.time() - start_strategy_execute
            return None
        else:
            if self.strategy_steps < 40:
                angle = 0
                if self.respawn == self.start_positions[2]:
                    angle = self.me.get_angle_to(100, 3800)
                self.move_.turn = angle
                self.move_.speed = self.game.wizard_backward_speed

                self.strategy_time += time.time() - start_strategy_execute
                return None

        # in game-check, if stuck
        pass
        # in game-check, if stuck
        if self.me.x == self.PREVIOUS_POS[0] and self.me.y == self.PREVIOUS_POS[1]:
            if not self.FIGHTING:
                self.NO_MOVE += 1
                if self.NO_MOVE >= self.MAX_NO_MOVE:
                    print('I am stuck')
                    self.move_.turn = self.game.wizard_max_turn_angle
                    self.move_.strafe_speed = self.game.wizard_strafe_speed
                    if my_target:
                        distance = self.me.get_distance_to(my_target.x, my_target.y)
                        if distance <= self.me.cast_range:
                            if self.me.remaining_cooldown_ticks_by_action[2] <= 3:
                                angle = self.me.get_angle_to(my_target.x, my_target.y)
                                move.turn = angle
                                if abs(angle) < game.staff_sector / 2:
                                    move.action = ActionType.MAGIC_MISSILE
                                    move.cast_angle = angle
                                    move.min_cast_distance = distance - my_target.radius + game.magic_missile_radius

                                self.strategy_time += time.time() - start_strategy_execute
                                return None
                    return None
        else:
            self.NO_MOVE = 0
        self.PREVIOUS_POS = [self.me.x, self.me.y]

        pass
        # low hp run back
        if len(enemies['minion']) == 0 and len(enemies['wizard']) == 0 and len(enemies['building']) == 0:
            if self.MOVE_LOW_HP > 0:
                self.MOVE_LOW_HP -= 1
                self.move_to_waypoint(self.last_waypoint(), False)

                if self.strategy_steps % 20 == 0:
                    print('go back - low hp: x: %s y: %s for %s ticks' %
                          (round(self.me.x, 1), round(self.me.y, 1), self.MOVE_LOW_HP))
                if my_target:
                    distance = self.me.get_distance_to(my_target.x, my_target.y)
                    if distance <= self.me.cast_range:
                        if self.me.remaining_cooldown_ticks_by_action[2] == 0:
                            angle = self.me.get_angle_to(my_target.x, my_target.y)
                            move.turn = angle
                            if abs(angle) < game.staff_sector / 2:
                                move.action = ActionType.MAGIC_MISSILE
                                move.cast_angle = angle
                                move.min_cast_distance = distance - my_target.radius + game.magic_missile_radius

        else:
            if self.me.life < self.me.max_life * self.LOW_HP_FACTOR[0]:
                if self.me.life < self.me.max_life * self.LOW_HP_FACTOR[1]:
                    if self.me.life < self.me.max_life * 0.12:
                        print('CRITICAL HP LEVEL')
                    self.MOVE_LOW_HP = 100
                    if self.strategy_steps % 10 == 0:
                        print('go back - low hp: x: %s y: % s' % (round(self.me.x, 1), round(self.me.y, 1)))
                    self.move_to_waypoint(self.last_waypoint(), False)
                    if my_target:
                        distance = self.me.get_distance_to(my_target.x, my_target.y)
                        if distance <= self.me.cast_range:
                            if self.me.remaining_cooldown_ticks_by_action[2] == 0:
                                angle = self.me.get_angle_to(my_target.x, my_target.y)
                                move.turn = angle
                                if abs(angle) < game.staff_sector / 2:
                                    move.action = ActionType.MAGIC_MISSILE
                                    move.cast_angle = angle
                                    move.min_cast_distance = distance - my_target.radius + game.magic_missile_radius

                self.strategy_time += time.time() - start_strategy_execute
                return None

        pass

        # bonus collection: if nobody collects in game
        if self.BONUS_EXIST:
            if self.lane == LaneType.TOP:
                if (self.CURRENT_WAYPOINT_INDEX > 6) and (self.CURRENT_WAYPOINT_INDEX < 11):
                    if len(enemies['wizard']) > 0:
                        for enemy_wiz in enemies['wizard']:
                            if (enemy_wiz.x > 1100) and (enemy_wiz.x < 1300) and (enemy_wiz.y > 1100) and (enemy_wiz.y < 1300):
                                if enemy_wiz.life > self.me.life:
                                    self.BONUS_EXIST = False

                    # self.move_to_waypoint(self.BONUS_POINT_TOP, True)
                    self.move_.turn = self.me.get_angle_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1])
                    self.move_.speed = self.game.wizard_forward_speed
                    self.move_.action = ActionType.MAGIC_MISSILE
                    self.move_.cast_angle = self.me.get_angle_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1])
                    self.move_.min_cast_distance = 400
                    if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) < 500:
                        if self.world.bonuses:
                            for bonus in self.world.bonuses:
                                if bonus.x == self.BONUS_POINT_TOP[0] and bonus.y == self.BONUS_POINT_TOP[0]:
                                    self.BONUS_EXIST = True
                                    break
                                self.BONUS_EXIST = False
                        else:
                            self.BONUS_EXIST = False

                    if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) <= 55:
                        if self.me.statuses:
                            self.BONUS_COUNT += 1
                            my_status = self.me.statuses[0]
                            print(my_status.type, my_status.remaining_duration_ticks)

                    self.strategy_time += time.time() - start_strategy_execute
                    return None
                else:
                    # collect bonus if at 11 and 12 position
                    if (self.CURRENT_WAYPOINT_INDEX >= 11) and (self.CURRENT_WAYPOINT_INDEX < 13):
                        print('go back to waypoint[8]')
                        if not self.BONUS_GO:
                            self.move_to_waypoint(self.waypoints[8], False)
                        if self.me.get_distance_to(self.waypoints[8][0], self.waypoints[8][1]) < 120:
                            print('waypoint[8] active: goto bonus')
                            self.BONUS_GO = True
                        if self.BONUS_GO:
                            self.move_.turn = self.me.get_angle_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1])
                            self.move_.speed = self.game.wizard_forward_speed
                            self.move_.action = ActionType.MAGIC_MISSILE
                            self.move_.cast_angle = self.me.get_angle_to(self.BONUS_POINT_TOP[0],
                                                                         self.BONUS_POINT_TOP[1])
                            self.move_.min_cast_distance = 400
                            if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) < 500:
                                if self.world.bonuses:
                                    for bonus in self.world.bonuses:
                                        if bonus.x == self.BONUS_POINT_TOP[0] and bonus.y == self.BONUS_POINT_TOP[0]:
                                            self.BONUS_EXIST = True
                                            break
                                        self.BONUS_EXIST = False
                                        self.BONUS_GO = False
                                        self.CURRENT_WAYPOINT_INDEX = 8
                                else:
                                    self.BONUS_EXIST = False
                                    self.BONUS_GO = False
                                    self.CURRENT_WAYPOINT_INDEX = 8

                            if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) <= 55:
                                if self.me.statuses:
                                    self.BONUS_COUNT += 1
                                    self.BONUS_GO = False
                                    my_status = self.me.statuses[0]
                                    print(my_status.type, my_status.remaining_duration_ticks)

                            self.strategy_time += time.time() - start_strategy_execute
                            return None
                        self.strategy_time += time.time() - start_strategy_execute
                        return None

            if self.lane == LaneType.BOTTOM:
                if (self.CURRENT_WAYPOINT_INDEX > 6) and (self.CURRENT_WAYPOINT_INDEX < 11):
                    if len(enemies['wizard']) > 0:
                        for enemy_wiz in enemies['wizard']:
                            if (enemy_wiz.x > 2700) and (enemy_wiz.x < 2900) and (enemy_wiz.y > 2700) and (enemy_wiz.y < 2900):
                                if enemy_wiz.life > self.me.life:
                                    self.BONUS_EXIST = False

                    # self.move_to_waypoint(self.BONUS_POINT_BOT, True)
                    self.move_.turn = self.me.get_angle_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1])
                    self.move_.speed = self.game.wizard_forward_speed
                    self.move_.action = ActionType.MAGIC_MISSILE
                    self.move_.cast_angle = self.me.get_angle_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1])
                    self.move_.min_cast_distance = 400
                    if self.me.get_distance_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1]) < 500:
                        if self.world.bonuses:
                            for bonus in self.world.bonuses:
                                if bonus.x == self.BONUS_POINT_BOT[0] and bonus.y == self.BONUS_POINT_BOT[0]:
                                    self.BONUS_EXIST = True
                                    break
                                self.BONUS_EXIST = False
                        else:
                            self.BONUS_EXIST = False

                    if self.me.get_distance_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1]) <= 55:
                        if self.me.statuses:
                            my_status = self.me.statuses[0]
                            print(my_status.type, my_status.remaining_duration_ticks)
                            self.BONUS_COUNT += 1

                    self.strategy_time += time.time() - start_strategy_execute
                    return None

                # collect bonus if at 11 and 12 position
                if (self.CURRENT_WAYPOINT_INDEX >= 11) and (self.CURRENT_WAYPOINT_INDEX < 13):
                    print('go back to waypoint[8]')
                    if not self.BONUS_GO:
                        self.move_to_waypoint(self.waypoints[8], False)
                    if self.me.get_distance_to(self.waypoints[8][0], self.waypoints[8][1]) < 120:
                        print('waypoint[8] active: goto bonus')
                        self.BONUS_GO = True
                    if self.BONUS_GO:
                        self.move_.turn = self.me.get_angle_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1])
                        self.move_.speed = self.game.wizard_forward_speed
                        self.move_.action = ActionType.MAGIC_MISSILE
                        self.move_.cast_angle = self.me.get_angle_to(self.BONUS_POINT_BOT[0],
                                                                     self.BONUS_POINT_BOT[1])
                        self.move_.min_cast_distance = 400
                        if self.me.get_distance_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1]) < 500:
                            if self.world.bonuses:
                                for bonus in self.world.bonuses:
                                    if bonus.x == self.BONUS_POINT_BOT[0] and bonus.y == self.BONUS_POINT_BOT[0]:
                                        self.BONUS_EXIST = True
                                        break
                                    self.BONUS_EXIST = False
                                    self.BONUS_GO = False
                                    self.CURRENT_WAYPOINT_INDEX = 8
                            else:
                                self.BONUS_EXIST = False
                                self.BONUS_GO = False
                                self.CURRENT_WAYPOINT_INDEX = 8

                        if self.me.get_distance_to(self.BONUS_POINT_BOT[0], self.BONUS_POINT_BOT[1]) <= 55:
                            if self.me.statuses:
                                self.BONUS_COUNT += 1
                                self.BONUS_GO = False
                                my_status = self.me.statuses[0]
                                print(my_status.type, my_status.remaining_duration_ticks)

                        self.strategy_time += time.time() - start_strategy_execute
                        return None
                    self.strategy_time += time.time() - start_strategy_execute
                    return None

        # end bonus collection
        pass

        # bonus collection: simple option
        # if self.strategy_steps % 2501 == 1:
        #     self.BONUS_EXIST = True
        #     print('Bonus activated')
        #
        # if self.BONUS_EXIST:
        #     if self.lane == LaneType.TOP:
        #         if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) < 1600:
        #             if (self.CURRENT_WAYPOINT_INDEX >= 6) and (self.CURRENT_WAYPOINT_INDEX <= 8):
        #                 # check if wizard here
        #                 # if minion here
        #                 # waypoint system add here
        #                 self.move_.turn = self.me.get_angle_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1])
        #                 self.move_.speed = self.MAX_SPEED
        #                 self.move_.action = ActionType.MAGIC_MISSILE
        #                 self.move_.cast_angle = self.me.get_angle_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1])
        #                 self.move_.min_cast_distance = 10
        #                 if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) < 600:
        #                     if self.world.bonuses:
        #                         for bonus in self.world.bonuses:
        #                             if bonus.x == self.BONUS_POINT_TOP[0] and bonus.y == self.BONUS_POINT_TOP[0]:
        #                                 self.BONUS_EXIST = True
        #                                 break
        #                             self.BONUS_EXIST = False
        #                     else:
        #                         self.BONUS_EXIST = False
        #
        #                 if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) <= 55:
        #                     if self.me.statuses:
        #                         my_status = self.me.statuses[0]
        #                         print(my_status.type, my_status.remaining_duration_ticks)
        #
        #                 return None
        #
        # if self.lane == LaneType.TOP:
        #     if self.me.get_distance_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1]) <= 600:
        #         self.move_.turn = self.me.get_angle_to(350, 450)
        #         self.move_.speed = self.MAX_SPEED
        #         self.move_.action = ActionType.MAGIC_MISSILE
        #         self.move_.cast_angle = self.me.get_angle_to(self.BONUS_POINT_TOP[0], self.BONUS_POINT_TOP[1])
        #         self.move_.min_cast_distance = 10
        #         return None
        # # stop bonus collection -------------------------------------

        pass
        # new limit range function ----------------------------------
        if orc:
            if self.me.get_distance_to(orc.x, orc.y) <= self.ENEMIES_RANGE_LIMIT[3]:
                self.RANGE_LIMIT_ACTIVE = True
        if fetish:
            if self.me.get_distance_to(fetish.x, fetish.y) <= self.ENEMIES_RANGE_LIMIT[2]:
                self.RANGE_LIMIT_ACTIVE = True
        if building:
            if self.me.get_distance_to(building.x, building.y) <= self.ENEMIES_RANGE_LIMIT[1]:
                self.RANGE_LIMIT_ACTIVE = True
        if wizard:
            if self.me.get_distance_to(wizard.x, wizard.y) <= self.ENEMIES_RANGE_LIMIT[0]:
                self.RANGE_LIMIT_ACTIVE = True

        if self.RANGE_LIMIT_ACTIVE:
            # attack if can:
            if my_target:
                self.FIGHTING = True
                distance = self.me.get_distance_to(my_target.x, my_target.y)
                if distance <= self.me.cast_range:
                    if self.me.remaining_cooldown_ticks_by_action[2] <= 5:
                        angle = self.me.get_angle_to(my_target.x, my_target.y)
                        move.turn = angle
                        if abs(angle) < game.staff_sector / 2:
                            move.action = ActionType.MAGIC_MISSILE
                            move.cast_angle = angle
                            move.min_cast_distance = distance - my_target.radius + game.magic_missile_radius

                        self.strategy_time += time.time() - start_strategy_execute
                        return None
            # go back
            waypoint = self.last_waypoint()
            angle = self.me.get_angle_to(waypoint[0], waypoint[1])
            self.move_.turn = -angle
            self.move_.speed = -self.game.wizard_backward_speed
            self.RANGE_LIMIT_ACTIVE = False

            self.strategy_time += time.time() - start_strategy_execute
            return None
        # new limit range function ----------------------------------
        pass

        # # old limit range function: ---------------------------------
        # # staying close to frontier - refactor than
        # if self.ENEMY_IN_RANGE_TICK > 0:
        #     # if self.lane == LaneType.TOP:
        #     if self.me.x < 100:
        #         angle = self.me.get_angle_to(self.me.x, self.me.y + self.BACK_DISTANCE)
        #         self.move_.turn = angle
        #         self.move_.speed = self.game.wizard_backward_speed
        #     elif self.me.y < 100:
        #         angle = self.me.get_angle_to(self.me.x, self.me.y + self.BACK_DISTANCE)
        #         self.move_.turn = angle
        #         self.move_.speed = self.game.wizard_backward_speed
        #     else:
        #         self.move_.speed = -self.game.wizard_backward_speed
        #     self.ENEMY_IN_RANGE_TICK -= 1
        #
        #     # switch to the best enemy
        #     nearest_enemy_wizard = self.get_closest_or_with_low_hp_enemy_wizard_in_attack_range()
        #     if nearest_enemy_wizard is not None:
        #         my_target = nearest_enemy_wizard
        #     else:
        #         my_target = self.get_nearest_target_in_my_visible_range()
        #
        #     if my_target:
        #         self.FIGHTING = True
        #         distance = self.me.get_distance_to(my_target.x, my_target.y)
        #         if distance <= self.me.cast_range:
        #             angle = self.me.get_angle_to(my_target.x, my_target.y)
        #             move.turn = angle
        #             if abs(angle) < game.staff_sector / 2:
        #                 if self.me.remaining_cooldown_ticks_by_action[2] == 0:
        #                     move.min_cast_distance = distance - my_target.radius - 10
        #                     move.action = ActionType.MAGIC_MISSILE
        #                     move.cast_angle = angle
        #     return None
        #
        # # set a flag if too close to the enemies
        # # switch to the best enemy
        # nearest_enemy_wizard = self.get_closest_or_with_low_hp_enemy_wizard_in_attack_range()
        # if nearest_enemy_wizard is not None:
        #     my_target = nearest_enemy_wizard
        # else:
        #     my_target = self.get_nearest_target_in_my_visible_range()
        # the_closest = self.get_closest_enemy()
        # # TODO add obstacles check
        # if the_closest is not None:
        #     self.FIGHTING = True
        #     if self.me.remaining_cooldown_ticks_by_action[2] == 0 and my_target is not None:
        #         if self.me.get_distance_to(my_target.x, my_target.y) <= self.me.cast_range:
        #             angle_fire = self.me.get_angle_to(my_target.x, my_target.y)
        #             if abs(angle_fire) < game.staff_sector / 2:
        #                 move.action = ActionType.MAGIC_MISSILE
        #                 move.cast_angle = self.me.get_angle_to(my_target.x, my_target.y)
        #                 move.min_cast_distance = self.me.get_distance_to(my_target.x, my_target.y) - \
        #                                          my_target.radius - self.game.magic_missile_radius
        #     if self.me.life == self.me.max_life:
        #         self.ENEMY_IN_RANGE_TICK = 1
        #     else:
        #         self.ENEMY_IN_RANGE_TICK = 40
        #     print('range limit active, me x: %s, y: %s, HP - %s' % (round(self.me.x, 1), round(self.me.y, 1),
        #                                                             self.me.life))
        #     delta_x = self.me.x - the_closest.x
        #     delta_y = self.me.y - the_closest.y
        #     angle = None
        #
        #     # I
        #     if delta_y > 0 and abs(delta_x) <= self.BACK_ZONE:
        #         if self.me.y > 3800:
        #             angle = self.me.get_angle_to(self.me.x, 3900)
        #         else:
        #             angle = self.me.get_angle_to(self.me.x, self.me.y + self.BACK_DISTANCE)
        #     # II
        #     elif delta_x < 0 and abs(delta_y) <= self.BACK_ZONE:
        #         if self.me.x <= 200:
        #             angle = self.me.get_angle_to(self.me.x, self.me.y - self.BACK_DISTANCE * 2)
        #         else:
        #             angle = self.me.get_angle_to(self.me.x - self.BACK_DISTANCE, self.me.y)
        #
        #     if angle is None:
        #         self.move_.turn = -self.me.angle
        #     else:
        #         self.move_.turn = -angle
        #
        #     self.move_.speed = -self.game.wizard_backward_speed
        #     return None
        # # old limit range function: ---------------------------------

        pass
        # if on the edge of range and nothing triggers
        # attack something in range
        if my_target:
            self.FIGHTING = True
            distance = self.me.get_distance_to(my_target.x, my_target.y)
            if distance - my_target.radius <= self.me.cast_range:
                angle = self.me.get_angle_to(my_target.x, my_target.y)
                move.turn = angle
                if abs(angle) < game.staff_sector / 2:
                    if self.me.remaining_cooldown_ticks_by_action[2] == 0:
                        move.action = ActionType.MAGIC_MISSILE
                        move.cast_angle = angle
                        move.min_cast_distance = distance - my_target.radius + game.magic_missile_radius - 10

        # nothing to do - go further + if this is beginning wait for a minion wave
        self.FIGHTING = False

        if self.strategy_steps > self.MINION_STAY[0]:
            self.move_to_waypoint(self.next_waypoint(), direction=True)
        else:
            if self.CURRENT_WAYPOINT_INDEX == self.MINION_STAY[1] and self.strategy_steps < self.MINION_STAY[0]:
                if self.strategy_steps % 20 == 0:
                    print('Waiting for a minion wave')

                self.strategy_time += time.time() - start_strategy_execute
                return None
            else:
                self.move_to_waypoint(self.next_waypoint(), direction=True)
                self.strategy_time += time.time() - start_strategy_execute

    def initialize_strategy(self, game, me):
        random.seed(game.random_seed)
        map_size = game.map_size

        self.respawn = [me.x, me.y]
        self.PREVIOUS_POS = self.respawn
        self.bot_time = time.time()

        self.start_positions.append([100, 3700])
        self.start_positions.append([300, 3900])
        self.start_positions.append([200, 3800])
        self.start_positions.append([300, 3800])
        self.start_positions.append([200, 3700])

        self.waypoints_top.append([50, map_size - 50])
        self.waypoints_top.append([map_size - 3800, map_size - 1100])
        self.waypoints_top.append([map_size - 3800, map_size - 1400])
        self.waypoints_top.append([map_size - 3750, map_size - 1800])
        self.waypoints_top.append([map_size - 3800, map_size - 2200])
        self.waypoints_top.append([map_size - 3800, map_size - 2800])
        self.waypoints_top.append([map_size - 3800, map_size - 3200])  # wait wave
        self.waypoints_top.append([map_size - 3750, map_size - 3500])
        self.waypoints_top.append([map_size - 3700, map_size - 3650])
        self.waypoints_top.append([map_size - 3500, map_size - 3800])
        self.waypoints_top.append([map_size - 3200, map_size - 3800])
        self.waypoints_top.append([map_size - 2800, map_size - 3800])
        self.waypoints_top.append([map_size - 2400, map_size - 3800])
        self.waypoints_top.append([map_size - 2000, map_size - 3800])
        self.waypoints_top.append([map_size - 1600, map_size - 3800])
        self.waypoints_top.append([map_size - 1200, map_size - 3800])
        self.waypoints_top.append([map_size - 900, map_size - 3800])

        self.waypoints_bot.append([50, map_size - 50])
        self.waypoints_bot.append([map_size - 3100, map_size - 200])
        self.waypoints_bot.append([map_size - 2600, map_size - 200])
        self.waypoints_bot.append([map_size - 2200, map_size - 200])
        self.waypoints_bot.append([map_size - 1800, map_size - 200])
        self.waypoints_bot.append([map_size - 1200, map_size - 200])
        self.waypoints_bot.append([map_size - 800, map_size - 200])  # stay here
        self.waypoints_bot.append([map_size - 500, map_size - 350])
        self.waypoints_bot.append([map_size - 350, map_size - 300])
        self.waypoints_bot.append([map_size - 200, map_size - 500])
        self.waypoints_bot.append([map_size - 200, map_size - 800])
        self.waypoints_bot.append([map_size - 200, map_size - 1200])
        self.waypoints_bot.append([map_size - 200, map_size - 1600])
        self.waypoints_bot.append([map_size - 200, map_size - 2000])
        self.waypoints_bot.append([map_size - 200, map_size - 2400])
        self.waypoints_bot.append([map_size - 200, map_size - 2800])
        self.waypoints_bot.append([map_size - 200, map_size - 3100])

        self.waypoints_mid.append([50, map_size - 50])
        self.waypoints_mid.append([map_size - 3800, map_size - 200])
        self.waypoints_mid.append([map_size - 3800, map_size - 800])
        self.waypoints_mid.append([map_size - 3200, map_size - 800])
        self.waypoints_mid.append([map_size - 3000, map_size - 800])
        self.waypoints_mid.append([map_size - 2850, map_size - 1000])
        self.waypoints_mid.append([map_size - 2750, map_size - 1250])
        self.waypoints_mid.append([map_size - 2500, map_size - 1500])
        self.waypoints_mid.append([map_size - 2250, map_size - 1750])
        self.waypoints_mid.append([map_size - 2000, map_size - 2000])
        self.waypoints_mid.append([map_size - 1750, map_size - 2000])
        self.waypoints_mid.append([map_size - 1500, map_size - 2500])
        self.waypoints_mid.append([map_size - 1250, map_size - 2750])
        self.waypoints_mid.append([map_size - 1000, map_size - 3000])
        self.waypoints_mid.append([map_size - 800, map_size - 3200])
        self.waypoints_mid.append([map_size - 400, map_size - 3600])
        self.waypoints_mid.append([map_size - 200, map_size - 3800])

        self.LAST_WAYPOINT_INDEX = 16

        # if self.respawn == self.start_positions[0] or self.respawn == self.start_positions[4]:
        #     self.waypoints.append([50, map_size - 50])
        #     self.waypoints.append([map_size - 3800, map_size - 1100])
        #     self.waypoints.append([map_size - 3800, map_size - 1400])
        #     self.waypoints.append([map_size - 3750, map_size - 1800])
        #     self.waypoints.append([map_size - 3800, map_size - 2200])
        #     self.waypoints.append([map_size - 3800, map_size - 2800])
        #     self.waypoints.append([map_size - 3800, map_size - 3200])    # wait wave
        #     self.waypoints.append([map_size - 3750, map_size - 3500])
        #     self.waypoints.append([map_size - 3700, map_size - 3650])
        #     self.waypoints.append([map_size - 3500, map_size - 3800])
        #     self.waypoints.append([map_size - 3200, map_size - 3800])
        #     self.waypoints.append([map_size - 2800, map_size - 3800])
        #     self.waypoints.append([map_size - 2400, map_size - 3800])
        #     self.waypoints.append([map_size - 2000, map_size - 3800])
        #     self.waypoints.append([map_size - 1600, map_size - 3800])
        #     self.waypoints.append([map_size - 1200, map_size - 3800])
        #     self.waypoints.append([map_size - 800, map_size - 3800])
        #     self.waypoints.append([map_size - 200, map_size - 3800])
        #     self.lane = LaneType.TOP
        #     self.LAST_WAYPOINT_INDEX = 17
        #     self.bonus_waypoints.append([500, 500])
        #     self.bonus_waypoints.append([800, 800])
        #     self.bonus_waypoints.append([1160, 1160])
        # elif self.respawn == self.start_positions[1] or self.respawn == self.start_positions[3]:
        #     self.waypoints.append([50, map_size - 50])
        #     self.waypoints.append([map_size - 3100, map_size - 200])
        #     self.waypoints.append([map_size - 2600, map_size - 200])
        #     self.waypoints.append([map_size - 2200, map_size - 200])
        #     self.waypoints.append([map_size - 1800, map_size - 200])
        #     self.waypoints.append([map_size - 1200, map_size - 200])
        #     self.waypoints.append([map_size - 800, map_size - 200])  # stay here
        #     self.waypoints.append([map_size - 500, map_size - 350])
        #     self.waypoints.append([map_size - 350, map_size - 300])
        #     self.waypoints.append([map_size - 200, map_size - 500])
        #     self.waypoints.append([map_size - 200, map_size - 800])
        #     self.waypoints.append([map_size - 200, map_size - 1200])
        #     self.waypoints.append([map_size - 200, map_size - 1600])
        #     self.waypoints.append([map_size - 200, map_size - 2000])
        #     self.waypoints.append([map_size - 200, map_size - 2400])
        #     self.waypoints.append([map_size - 200, map_size - 2800])
        #     self.waypoints.append([map_size - 200, map_size - 3200])
        #     self.waypoints.append([map_size - 200, map_size - 3800])
        #     self.lane = LaneType.BOTTOM
        #     self.LAST_WAYPOINT_INDEX = 17
        # elif self.respawn == self.start_positions[2]:
        #     self.waypoints.append([50, map_size - 50])
        #     self.waypoints.append([map_size - 3800, map_size - 1100])
        #     self.waypoints.append([map_size - 3800, map_size - 1400])
        #     self.waypoints.append([map_size - 3750, map_size - 1800])
        #     self.waypoints.append([map_size - 3800, map_size - 2200])
        #     self.waypoints.append([map_size - 3800, map_size - 2800])
        #     self.waypoints.append([map_size - 3800, map_size - 3200])    # wait wave
        #     self.waypoints.append([map_size - 3750, map_size - 3500])
        #     self.waypoints.append([map_size - 3700, map_size - 3650])
        #     self.waypoints.append([map_size - 3500, map_size - 3800])
        #     self.waypoints.append([map_size - 3200, map_size - 3800])
        #     self.waypoints.append([map_size - 2800, map_size - 3800])
        #     self.waypoints.append([map_size - 2400, map_size - 3800])
        #     self.waypoints.append([map_size - 2000, map_size - 3800])
        #     self.waypoints.append([map_size - 1600, map_size - 3800])
        #     self.waypoints.append([map_size - 1200, map_size - 3800])
        #     self.waypoints.append([map_size - 800, map_size - 3800])
        #     self.waypoints.append([map_size - 200, map_size - 3800])
        #     self.lane = LaneType.TOP
        #     self.LAST_WAYPOINT_INDEX = 17
        #     self.bonus_waypoints.append([500, 500])
        #     self.bonus_waypoints.append([800, 800])
        #     self.bonus_waypoints.append([1160, 1160])

    def initialize_tick(self, world, game, me, move):
        self.world = world
        self.game = game
        self.me = me
        self.move_ = move
        self.strategy_steps += 1

        if self.strategy_steps % 2400 == 0:
            self.BONUS_EXIST = True
            print('Bonus will appear soon')

        if self.strategy_steps - 1 + self.game.wizard_min_resurrection_delay_ticks == self.world.tick_index or \
           self.strategy_steps - 1 != self.world.tick_index:
            self.WAS_DEAD = True
            self.DEATH_COUNT += 1
            self.strategy_steps = self.world.tick_index + 1
            print('--------------------------------------')
            print('I was dead %s times' % self.DEATH_COUNT)
            print('--------------------------------------')
            self.MOVE_LOW_HP = 0

        if self.WAS_DEAD:
            lane = self.defense_need()
            if lane != self.lane:
                self.lane = lane
                if self.lane == LaneType.TOP:
                    self.waypoints = self.waypoints_top
                if self.lane == LaneType.BOTTOM:
                    self.waypoints = self.waypoints_bot
                if self.lane == LaneType.MIDDLE:
                    self.waypoints = self.waypoints_mid
                self.CURRENT_WAYPOINT_INDEX = 1
                print('Switch to defense line %s' % self.lane)

            self.CURRENT_WAYPOINT_INDEX = 1
            self.WAS_DEAD = False

    def get_the_closest_of_attack_range(self, enemies):
        # returns
        # enemy_wizard, enemy_tower, enemy_fetish, enemy_orc
        enemy_wizard, enemy_tower, enemy_fetish, enemy_orc = None, None, None, None
        if len(enemies['minion']) == 0 and len(enemies['wizard']) == 0 and len(enemies['building']) == 0:
            return enemy_wizard, enemy_tower, enemy_fetish, enemy_orc
        if len(enemies['wizard']) > 0:
            distance = 700
            enemy_wizard = enemies['wizard'][0]
            for enemy in enemies['wizard']:
                if self.me.get_distance_to(enemy_wizard.x, enemy_wizard.y) < distance:
                    enemy_wizard = enemy
                    distance = self.me.get_distance_to(enemy_wizard.x, enemy_wizard.y)
        if len(enemies['building']) == 1:
            enemy_tower = enemies['building'][0]
        if len(enemies['minion']) > 0:
            enemy_fetish, enemy_orc = None, None
            dist_orc, dist_fetish = 700, 700
            for minion in enemies['minion']:
                if minion.type == MinionType.FETISH_BLOWDART:
                    if self.me.get_distance_to(minion.x, minion.y) < dist_fetish:
                        enemy_fetish = minion
                        dist_fetish = self.me.get_distance_to(enemy_fetish.x, enemy_fetish.y)
                if minion.type == MinionType.ORC_WOODCUTTER:
                    if self.me.get_distance_to(minion.x, minion.y) < dist_orc:
                        enemy_orc = minion
                        dist_orc = self.me.get_distance_to(enemy_orc.x, enemy_orc.y)

        return enemy_wizard, enemy_tower, enemy_fetish, enemy_orc

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

    def next_waypoint(self):
        if self.CURRENT_WAYPOINT_INDEX == self.LAST_WAYPOINT_INDEX:
            return self.waypoints[self.LAST_WAYPOINT_INDEX]
        if self.me.get_distance_to(self.waypoints[self.CURRENT_WAYPOINT_INDEX][0],
                                   self.waypoints[self.CURRENT_WAYPOINT_INDEX][1]) < self.WAYPOINT_RADIUS_NEW:
            self.CURRENT_WAYPOINT_INDEX += 1
        return self.waypoints[self.CURRENT_WAYPOINT_INDEX]

    def last_waypoint(self):
        if self.CURRENT_WAYPOINT_INDEX == 0:
            return self.waypoints[0]
        if self.me.get_distance_to(self.waypoints[self.CURRENT_WAYPOINT_INDEX - 1][0],
                                   self.waypoints[self.CURRENT_WAYPOINT_INDEX - 1][1]) < self.WAYPOINT_RADIUS_NEW:
            self.CURRENT_WAYPOINT_INDEX -= 1
        return self.waypoints[self.CURRENT_WAYPOINT_INDEX - 1]

    def move_to_waypoint(self, waypoint, direction):
        self.debug_next_waypoint = waypoint
        if self.strategy_steps % 50 == 0:
            print('Waypoint %s, index %s' % (waypoint, self.CURRENT_WAYPOINT_INDEX))

        if direction:
            next_milestone = self.path_finder_forward(waypoint=waypoint)
        else:
            next_milestone = self.path_finder_backward(waypoint=waypoint)

        if self.strategy_steps % 50 == 0:
            print('Milestone %s' % next_milestone)
        if next_milestone:
            self.debug_next_milestone = next_milestone
            angle = self.me.get_angle_to(next_milestone[0], next_milestone[1])
            self.move_.turn = angle
            self.move_.speed = self.game.wizard_forward_speed
        else:
            print('No answer from pathfinder!')
            if waypoint:
                angle = self.me.get_angle_to(waypoint[0], waypoint[1])
                self.move_.turn = angle
                self.move_.speed = self.game.wizard_forward_speed
            else:
                print('WTF?? no waypoint send to --move_to_waypoint function--')

    # def get_next_waypoint(self):
    #     last_waypoint_index = len(self.waypoints) - 1
    #     last_waypoint = self.waypoints[last_waypoint_index]
    #
    #     for waypoint_index in range(0, last_waypoint_index - 1):
    #         waypoint = self.waypoints[waypoint_index]
    #         if self.me.get_distance_to(waypoint[0], waypoint[1]) <= self.WAYPOINT_RADIUS:
    #             return self.waypoints[waypoint_index + 1]
    #         if math.hypot(waypoint[0] - last_waypoint[0], waypoint[1] - last_waypoint[1]) < self.me.get_distance_to(
    #                                                       last_waypoint[0], last_waypoint[1]):
    #             return waypoint
    #
    # def get_previous_waypoint(self):
    #     first_waypoint = self.waypoints[0]
    #     for waypoint_index in range(len(self.waypoints) - 1, 0, -1):
    #         waypoint = self.waypoints[waypoint_index]
    #         if self.me.get_distance_to(waypoint[0], waypoint[1]) <= self.WAYPOINT_RADIUS:
    #             return self.waypoints[waypoint_index - 1]
    #         if math.hypot(waypoint[0] - first_waypoint[0], waypoint[1] - first_waypoint[1]) < self.me.get_distance_to(
    #                                                        first_waypoint[0], first_waypoint[1]):
    #             return waypoint
    #
    # def goto(self, waypoint):
    #     if self.strategy_steps % 10 == 0:
    #         print('Milestone %s' % waypoint)
    #
    #     # !!! True / False right direction
    #     waypoint_bfs = self.path_finder(waypoint, True)
    #
    #     if self.strategy_steps % 10 == 0:
    #         print(waypoint, waypoint_bfs)
    #     if waypoint_bfs:
    #         angle = self.me.get_angle_to(waypoint_bfs[0], waypoint_bfs[1])
    #         self.move_.turn = angle
    #         self.move_.speed = self.MAX_SPEED
    #     else:
    #         if waypoint:
    #             angle = self.me.get_angle_to(waypoint[0], waypoint[1])
    #             self.move_.turn = angle
    #             self.move_.speed = self.MAX_SPEED

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
                if self.me.get_distance_to(enemy.x, enemy.y) < self.me.get_distance_to(the_closest_enemy_wizard.x,
                                                                                       the_closest_enemy_wizard.y):
                    the_closest_enemy_wizard = enemy
            for enemy in enemy_wizards:
                if enemy.life < self.LOW_HP_ENEMY_SWITCH and self.me.get_distance_to(enemy.x, enemy.y) < \
                        self.ATTACK_RANGE:
                    return enemy
            return the_closest_enemy_wizard
        else:
            return None

    def get_tower_in_range(self):
        towers = []
        for target in self.world.buildings:
            if target.faction == self.me.faction:
                continue
            if self.me.get_distance_to(target.x, target.y) <= self.ATTACK_RANGE:
                towers.append(target)
        if len(towers) > 0:
            the_closest_tower = towers[0]
            for tower in towers:
                if self.me.get_distance_to(tower.x, tower.y) < self.me.get_distance_to(the_closest_tower.x,
                                                                                       the_closest_tower.y):
                    the_closest_tower = tower
            return the_closest_tower
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

    def path_finder_forward(self, waypoint):
        path_forward = time.time()
        start = [self.me.x, self.me.y]           # x:200 y:1000
        if waypoint:
            finish = [waypoint[0], waypoint[1]]      # x:200 y:600
        else:
            finish = self.waypoints[self.CURRENT_WAYPOINT_INDEX]

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
                line_x.append([net_x + step, net_y + step])
                # line_x.append([net_x + step, net_y + step])
            net_2d.append(line_x)

        # get obstacles
        obstacles = self.get_obstacles_in_zone([
            int(min(lb[0], lt[0]) + step), int(max(rb[0], rt[0]) - step),
            int(min(lt[1], rt[1]) + step), int(max(lb[1], rb[1]) - step)])

        self.debug_obstacles = obstacles
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

        self.graph_profile += time.time() - path_forward
        if start_node is None:
            # print('FORWARD: no start waypoint found')
            return self.waypoints[self.CURRENT_WAYPOINT_INDEX]

        if end_node is None:
            # print('FORWARD: no finish waypoint found')
            return self.waypoints[self.CURRENT_WAYPOINT_INDEX]

        # v_name = (int(start_node) // 100) - 1
        # h_name = int(start_node) % 100
        # next_coords = net_2d[v_name][h_name]
        #
        # v_name = (int(end_node) // 100) - 1
        # h_name = int(end_node) % 100
        # next_coords = net_2d[v_name][h_name]

        bfs_start = time.time()
        next_path = self.bfs(graph_to_search=graph, start=start_node, end=end_node)
        self.bfs_profile += time.time() - bfs_start
        del graph

        # return coordinates based on square name
        if next_path:
            if len(next_path) > 1:
                next_node = next_path[1]
                v_name = (int(next_node) // 100) - 1
                h_name = int(next_node) % 100
                next_coords = net_2d[v_name][h_name]

                self.debug_view_path = []
                for element in next_path:
                    v_name = (int(element) // 100) - 1
                    h_name = int(element) % 100
                    xy = net_2d[v_name][h_name]
                    self.debug_view_path.append(xy)
                return next_coords
            else:
                return waypoint

    def path_finder_backward(self, waypoint):
        path_backward = time.time()

        start = [self.me.x, self.me.y]           # x:200 y:2000
        if waypoint:
            finish = [waypoint[0], waypoint[1]]      # x:200 y:3000
        else:
            finish = self.waypoints[self.CURRENT_WAYPOINT_INDEX - 1]

        graph = IndirectedGraph()

        lt = [start[0] - self.PATH_FINDING_GRID, start[1] - self.PATH_FINDING_GRID]  # lb: x: -150 y: 1650
        rt = [start[0] + self.PATH_FINDING_GRID, start[1] - self.PATH_FINDING_GRID]  # rb: x: 550 y: 1650
        lb = [finish[0] - self.PATH_FINDING_GRID, finish[1] + self.PATH_FINDING_GRID]  # lt: x: -150 y: 3350
        rb = [finish[0] + self.PATH_FINDING_GRID, finish[1] + self.PATH_FINDING_GRID]  # lt: x: 550 y: 3350

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
                line_x.append([net_x + step, net_y + step])
            net_2d.append(line_x)

        # get obstacles
        obstacles = self.get_obstacles_in_zone([
            int(min(lb[0], lt[0]) + step), int(max(rb[0], rt[0]) - step),
            int(min(lt[1], rt[1]) + step), int(max(lb[1], rb[1]) - step)])

        self.debug_obstacles = obstacles

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

        self.graph_profile += time.time() - path_backward
        if start_node is None:
            # print('BACKWARD: no start waypoint found')
            return self.waypoints[self.CURRENT_WAYPOINT_INDEX - 1]

        if end_node is None:
            # print('BACKWARD: no finish waypoint found')
            return self.waypoints[self.CURRENT_WAYPOINT_INDEX - 1]

        bfs_start = time.time()
        next_path = self.bfs(graph_to_search=graph, start=start_node, end=end_node)
        self.bfs_profile += time.time() - bfs_start
        del graph

        # return coordinates based on square name
        if next_path:
            if len(next_path) > 1:
                next_node = next_path[1]
                v_name = (int(next_node) // 100) - 1
                h_name = int(next_node) % 100
                next_coords = net_2d[v_name][h_name]

                self.debug_view_path = []
                for element in next_path:
                    v_name = (int(element) // 100) - 1
                    h_name = int(element) % 100
                    xy = net_2d[v_name][h_name]
                    self.debug_view_path.append(xy)
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
            if squared_dist <= 1.42 * cell_radius ** 2:
                return True
            # if (obstacle.x + obstacle.radius < target_cell[0] - )
        return False

    @staticmethod
    def return_node(net, coords, cell_radius):
        if coords is not None:
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

    def get_a_line_to_push(self):
        we = []
        for target in self.world.wizards:
            if target.faction == self.me.faction:
                if target.x == self.me.x and target.y == self.me.y:
                    continue
                we.append(target)

        top_number, bot_number = 0, 0
        if we:
            for target in we:
                if target.x < 330 and target.y > 3000:
                    top_number += 1
                if target.x > 700 and target.y > 3650:
                    bot_number += 2
        if top_number < self.MIN_PUSH_AMOUNT:
            return LaneType.TOP
        if bot_number < self.MIN_PUSH_AMOUNT:
            return LaneType.BOTTOM
        return LaneType.TOP

    def defense_need(self):
        towers = []
        for tower in self.world.buildings:
            if tower.faction == self.me.faction:
                if tower.x == 400:
                    continue
                towers.append(tower)

        if len(towers) > 3:
            return None

        top_towers, bot_towers, mid_towers = 0, 0, 0
        for tower in towers:
            if tower.x < 360:
                top_towers += 1
            elif tower.y > 3640:
                bot_towers += 1
            if tower.x == 902:
                mid_towers += 1

        if mid_towers == 0:
            return LaneType.MIDDLE
        if top_towers == 0:
            return LaneType.TOP
        if bot_towers == 0:
            return LaneType.BOTTOM

        return self.lane
