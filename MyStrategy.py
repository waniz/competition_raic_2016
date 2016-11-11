from model.ActionType import ActionType
from model.Building import Building
from model.BuildingType import BuildingType
from model.Bonus import Bonus
from model.BonusType import BonusType
from model.Faction import Faction
from model.Game import Game
from model.LaneType import LaneType
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


class MyStrategy:
    # main call
    def move(self, me: Wizard, world: World, game: Game, move: Move):

        # self.check_top_lane_tower(me=me, world=world, game=game)
        t1_top_tower = self.get_top_tower_t1_coords(me=me, world=world)

        # TODO - add check my location and paths for forest
        my_char = Unit(me.id, me.x, me.y, me.speed_x, me.speed_y, me.angle, me.faction)
        print('My coordinates: x: %s, y: %s' % (me.x, me.y))
        print('Target coordinates: x: %s, y: %s' % (t1_top_tower['x'], t1_top_tower['y']))
        angle_to_target = my_char.get_angle_to(t1_top_tower['x'], t1_top_tower['y'])
        print('Angle to target: %s' % angle_to_target)
        if angle_to_target != me.angle:
            move.turn = angle_to_target - me.angle  #game.wizard_max_turn_angle

        self.go_to_location(me=me, target=t1_top_tower)

        # move.speed = game.wizard_forward_speed
        # move.strafe_speed = game.wizard_strafe_speed
        # move.turn = game.wizard_max_turn_angle
        # move.action = ActionType.MAGIC_MISSILE

    # ------ helper functions ---------------------------------------
    # TODO - check if it exists
    @staticmethod
    def get_top_tower_t1_coords(me, world):
        print('Function: get_top_tower_t1_coords')
        building_list = []
        print('My fraction: %s' % me.faction)
        for building in world.buildings:
            building_list.append([building.x, building.y])
            print('Building coordinates: x: %s, y: %s. Building type: %s' % (building.x, building.y, building.type))

        t1_tower = {'x': building_list[0][0], 'y': building_list[0][1]}
        if me.faction == Faction.ACADEMY:
            for pos in range(1, len(building_list)):
                if t1_tower['y'] > building_list[pos][1]:
                    t1_tower['x'], t1_tower['y'] = building_list[pos][0], building_list[pos][1]
        elif me.faction == Faction.RENEGADES:
            for pos in range(1, len(building_list)):
                if t1_tower['x'] > building_list[pos][0]:
                    t1_tower['x'], t1_tower['y'] = building_list[pos][0], building_list[pos][1]

        print('T1 tower is : x %s, y %s' % (t1_tower['x'], t1_tower['y']))
        print('')
        return t1_tower

    @staticmethod
    def go_to_location(me, target):
        my_char = Unit(me.id, me.x, me.y, me.speed_x, me.speed_y, me.angle, me.faction)
        print('Function: go_to_location')
        print('My coordinates: x: %s, y: %s' % (me.x, me.y))
        print('Target coordinates: x: %s, y: %s' % (target['x'], target['y']))
        angle_to_target = my_char.get_angle_to(target['x'], target['y'])
        print('Angle to target: %s' % angle_to_target)
        if angle_to_target != me.angle:
            move.turn = game.wizard_max_turn_angle

        print('')

    def if_bonus_exists(self, me, world, game):
        pass

    # ------ analisys functions -------------------------------------
    def simulate_next_tick_world(self):
        pass
