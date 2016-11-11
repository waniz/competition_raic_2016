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

from model.Wizard import Wizard
from model.World import World


class MyStrategy:
    # main call
    def move(self, me: Wizard, world: World, game: Game, move: Move):

        self.check_top_lane_tower(me=me, world=world, game=game)

        move.speed = game.wizard_forward_speed
        move.strafe_speed = game.wizard_strafe_speed
        move.turn = game.wizard_max_turn_angle
        move.action = ActionType.MAGIC_MISSILE

    # ------ helper functions ---------------------------------------
    def check_top_lane_tower(self, me, world, game):
        # if top line tower exists
        my_building = world.buildings[0]

        print(world.buildings[0])
        print(my_building)
        print(my_building.type)
        print(my_building.attack_range)
        print(my_building.x, my_building.y)


    def if_bonus_exists(self, me, world, game):
        pass

    # ------ analisys functions -------------------------------------
    def simulate_next_tick_world(self):
        pass
