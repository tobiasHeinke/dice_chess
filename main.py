# SPDX-License-Identifier: GPL-3.0-or-later

import math
import random

import bpy
from bpy.props import (
            BoolProperty,
            EnumProperty,
            IntProperty,
            StringProperty,
            )
from bpy.types import (
            Operator,
            Scene,
            )
import mathutils


class RDC_OT_board_history(Operator):
    bl_idname = 'rdc_game.board_history'
    bl_label = 'Game History'
    bl_description = 'Board history'

    action: EnumProperty(
        items=[
            ('UNDO', 'undo', 'undo'),
            ('REDO', 'redo', 'redo'),
        ]
    )

    def poll_action(self, context):
        if self.action == 'UNDO':
            return bpy.ops.ed.undo.poll()
        elif self.action == 'REDO':
            return bpy.ops.ed.redo.poll()
        return True

    def execute(self, context):
        if self.action == 'UNDO':
            bpy.ops.ed.undo()
        elif self.action == 'REDO':
            bpy.ops.ed.redo()
        return {'FINISHED'}


class RDC_OT_board(Operator):
    bl_idname = 'rdc_game.board'
    bl_label = 'Game Board'
    bl_description = 'Board actions'
    bl_options = {'UNDO',}

    action: EnumProperty(
        items=[
            ('INIT', 'init', 'init'),
            ('RANDOMIZE', 'randomize', 'randomize'),
            ('RESET', 'reset', 'reset'),
            ('GO', 'go', 'go'),
        ]
    )

    def execute(self, context):
        if self.action == 'RANDOMIZE':
            Board.randomize(context, self)
        elif self.action == 'RESET':
            Board.reset(context)
            Board.init(context)
        elif self.action == 'GO':
            Board.go(context)
        elif self.action == 'INIT':
            Board.init(context)
        return {'FINISHED'}


class Board():
    setup = "DDDKQDDD\n   RR   \n"
    piece_names = {"K": "King", "Q": "Queen", "R": "Rook", "D": "Dice"}

    @staticmethod
    def init(context):
        for obj in get_fuzzy(context, "Pieces").all_objects:
            piece = Piece.new(context, obj)
            piece.init(obj)
        context.scene.rdc_game_current_frame = 0
        context.scene.rdc_game_prev_active = ""
        context.scene.instr_import = ""
        context.scene.instr_export = ""

    @staticmethod
    def reset(context):
        context.scene.rdc_game_current_frame = 0
        bpy.context.scene.frame_set(context.scene.rdc_game_current_frame)
        coll_pieces = get_fuzzy(context, "Pieces")
        if coll_pieces is None:
            coll_pieces = bpy.data.collections.new("Pieces")
            context.scene.collection.children.link(coll_pieces)
        else:
            for obj in coll_pieces.all_objects:
                obj.select_set(True)
            bpy.ops.object.delete(use_global=True, confirm=False)

        for color in range(2):
            coll_type_color = get_fuzzy(context, ("Black", "White")[color],
                                        get_fuzzy(context, "Types"))
            coll_pieces_color = get_fuzzy(context, ("Black", "White")[color], coll_pieces)
            if coll_pieces_color is None:
                coll_pieces_color = bpy.data.collections.new(("Black", "White")[color])
                coll_pieces.children.link(coll_pieces_color)

            obj_names = {}
            for index_rank, rank in enumerate(Board.setup.splitlines()):
                index_rank = 7 * color + (-1 + bool(not color) * 2) * index_rank
                for index_file, file in enumerate(reversed(rank) if color else rank):
                    if file not in Board.piece_names.keys():
                        continue
                    name = Board.piece_names[file]
                    if name not in obj_names.keys():
                        obj_names[name] = get_fuzzy(context, name, coll_type_color).name

                    bpy.ops.object.add_named(linked=True, name=obj_names[name])
                    obj = context.active_object
                    coll_pieces_color.objects.link(obj)
                    obj.location = (index_file, index_rank, obj.location.z)
                    obj.keyframe_insert(data_path='location')
                    obj.keyframe_insert(data_path='rotation_euler')

    @staticmethod
    def intersect_board(context, obj=None, loc=None):
        if loc is None:
            if obj is not None:
                loc = obj.location
            elif context.active_object is not None:
                loc = context.active_object.location
            else:
                return
        loc = tuple(map(round, loc))
        for other in get_fuzzy(context, "Pieces").all_objects:
            loc_other = tuple(map(round, other.location))
            if (loc_other == loc and (obj is None or other.name != obj.name)):
                return other
        return None

    @staticmethod
    def is_in_bounds(loc):
        loc = tuple(map(round, loc))
        return (loc[0] >= 0 and loc[0] <= 7 and loc[1] >= 0 and loc[1] <= 7)

    @staticmethod
    def intersect_out(context, obj):
        x = 0
        while True:
            for other in get_fuzzy(context, "Pieces").all_objects:
                if round(other.location.y) not in (9, -2):
                    continue
                if (round(other.location.x) == x and
                        round(other.location.y) == round(obj.location.y) and
                        other.name != obj.name):
                    x += 1
                    break
            else:
                break
        obj.location.x = x
        obj.keyframe_insert(data_path='location')

    @staticmethod
    def get_color(context, obj=None):
        if obj is None:
            obj = context.active_object
        for color in range(2):
            for other in get_fuzzy(context, ("Black", "White")[color],
                                   get_fuzzy(context, "Pieces")).objects:
                if obj.name == other.name:
                    return bool(color)
        return False

    @staticmethod
    def get_type(obj):
        for value in Board.piece_names.values():
            if obj.name.startswith(value):
                return value

    @staticmethod
    def sum_up(context, flip=True):
        sums = [0, 0]
        for color in range(2):
            for other in get_fuzzy(context, ("Black", "White")[color],
                                   get_fuzzy(context, "Pieces")).objects:
                if not Board.is_in_bounds(other.location):
                    continue
                if Board.get_type(other) in ("Dice", "Queen"):
                    sums[color] += other["value"]
        return (tuple(sums) if not flip or context.active_object is None or
                not Board.get_color(context) else (sums[1], sums[0]))

    @staticmethod
    def loc_to_algebraic(context, loc=None):
        if loc is None:
            if context.active_object is None:
                return ""
            loc = context.active_object.location
        loc = tuple(map(round, loc))
        return chr(loc[0] + 65) + str(loc[1] + 1)

    @staticmethod
    def algebraic_to_loc(algebraic):
        if (len(algebraic) != 2 or
                not algebraic[0].isalpha() or not algebraic[1].isdigit()):
            raise ValueError("Invalid algebraic notation: " + algebraic)

        return (ord(algebraic[0].upper()) - 65, int(algebraic[1]) - 1, 0)

    @staticmethod
    def start(context, op):
        sums = Board.sum_up(context, flip=False)
        if sums[0] != sums[1]:
            start_color = bool(sums[0] > sums[1])
        else:
            sides = []
            for color in range(2):
                values = [1 for _ in range(0, 7)]
                for file in range(0, 7):
                    obj = Board.intersect_board(context, loc=(file, (0, 7)[color]))
                    if not obj:
                        continue
                    if color: file = 7 - file
                    file -= 4
                    if file < 0: file = 7 + file
                    values[file] = obj["value"]

                sides.append(values)
            for values in zip(*sides):
                if values[0] != values[1]:
                    start_color = bool(values[0] > values[1])
                    break
            else:
                start_color = False

        op.report({'INFO'}, ("Black", "White")[start_color] + " moves first!")
        context.scene.rdc_game_prev_active = get_fuzzy(
            context, ("Black", "White")[not start_color],
            get_fuzzy(context, "Pieces")).objects[0].name
        return start_color

    @staticmethod
    def end(context, obj, collider, op):
        if collider is not None and Board.get_type(collider) == "King":
            end_color = Board.get_color(context, obj)
            op.report({'INFO'}, ("Black", "White")[end_color] + " wins!!!")
            context.scene.rdc_game_prev_active = collider.name
            return end_color

    @staticmethod
    def randomize(context, op):
        random.seed(context.scene.seed if len(context.scene.seed) != 0 else None, version=2)
        for obj in get_fuzzy(context, "Pieces").all_objects:
            piece = Piece.new(context, obj)
            if hasattr(piece, "randomize"):
                piece.randomize(obj)
        Board.start(context, op)

    @staticmethod
    def poll_instr(self, context):
        instr = context.scene.instr_import
        instr = instr.strip().replace(' ', '')
        if len(instr) == 0 or len(instr) % 2 != 0:
            return False
        instr = [instr[i:i + 2] for i in range(0, len(instr), 2)]
        for index, algebraic in enumerate(instr):
            for index_rec, rec in enumerate(instr):
                if index != index_rec and rec == algebraic:
                    return False

        obj = None
        prev = None
        for algebraic in instr:
            try:
                loc = Board.algebraic_to_loc(algebraic)
            except ValueError:
                return False
            if not Board.is_in_bounds(loc):
                return False
            if prev is None:
                obj = Board.intersect_board(context, loc=loc)
                if not obj:
                    return False
                if len(instr) - 1 != obj["value"]:
                    return False
                prev = loc
                continue

            piece = Piece.new(context, obj)
            delta = tuple(a - b for a, b in zip(prev, loc))
            action = piece.delta_to_action(context, obj, delta)
            valid = piece.poll_action(context, obj=obj, obj_loc=prev, action=action)
            if not valid:
                return False
            prev = loc
        return True

    @staticmethod
    def go(context):
        instr = context.scene.instr_import
        instr = instr.strip().replace(' ', '')
        instr = [instr[i:i + 2] for i in range(0, len(instr), 2)]
        obj = None
        prev = None
        for algebraic in instr:
            loc = Board.algebraic_to_loc(algebraic)
            if prev is None:
                obj = Board.intersect_board(context, loc=loc)
                for other in bpy.context.selected_objects:
                    other.select_set(False)
                context.view_layer.objects.active = obj
                obj.select_set(True)
            else:
                piece = Piece.new(context, obj)
                delta = tuple(a - b for a, b in zip(prev, loc))
                bpy.ops.object.rdc_game_piece(action=piece.delta_to_action(context, obj, delta))
            prev = loc


class RDC_OT_move_piece(Operator):
    bl_idname = 'object.rdc_game_piece'
    bl_label = 'Game Piece'
    bl_description = 'Move piece'
    bl_options = {'UNDO',}

    action: EnumProperty(
        items=[
            ('FORWARD', 'move forward', 'move forward'),
            ('FORWARD_RIGHT', 'move forward right', 'move forward right'),
            ('FORWARD_LEFT', 'move forward left', 'move forward left'),
            ('RIGHT', 'move right', 'move right'),
            ('LEFT', 'move left', 'move left'),
            ('BACKWARD', 'move backward', 'move backward'),
            ('BACKWARD_RIGHT', 'move backward right', 'move backward right'),
            ('BACKWARD_LEFT', 'move backward left', 'move backward left'),
        ]
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    @staticmethod
    def poll_action(self, context):
        piece = Piece.new(context)
        if piece is None:
            return False
        return piece.poll_action(context, action=self.action)

    def execute(self, context):
        bpy.context.scene.frame_set(context.scene.rdc_game_current_frame)
        piece = Piece.new(context)
        if not piece.poll_action(context, action=self.action):
            return {'CANCELLED'}
        piece.move(self, context, self.action)
        return {'FINISHED'}


class Piece():
    move_names = (
        'BACKWARD_LEFT', 'BACKWARD', 'BACKWARD_RIGHT',
        'LEFT', 'NONE', 'RIGHT',
        'FORWARD_LEFT', 'FORWARD', 'FORWARD_RIGHT')
    move_names_straight = set(name for index, name in enumerate(move_names) if index % 2 != 0)

    def __init__(self, obj):
        self.obj = obj

    @staticmethod
    def new(context, obj=None):
        if obj is None:
            obj = context.active_object
        obj_typ = Board.get_type(obj)
        if obj_typ == "Dice":
            return Dice(obj)
        elif obj_typ == "Queen":
            return Queen(obj)
        elif obj_typ == "Rook":
            return Rook(obj)
        elif obj_typ == "King":
            return King(obj)

    def init(self, obj):
        obj["value"] = 1
        obj["start"] = obj["value"]
        obj["counter"] = obj["value"]

    def reset(self, obj):
        obj["value"] = 1
        obj["start"] = obj["value"]
        obj["counter"] = obj["value"]

    def poll_action(self, context, obj=None, obj_loc=None, action=None):
        if action is None:
            action = self.action
        if obj is None:
            obj = context.active_object

        if context.scene.rdc_game_prev_active:
            prev = context.scene.collection.all_objects.get(context.scene.rdc_game_prev_active)
            if (prev.name == obj.name) == (prev["counter"] == prev["start"]):
                return None
            if (prev.name != obj.name and
                    Board.get_color(context, prev) == Board.get_color(context, obj)):
                return None
        if not self.is_in_move_set(action):
            return None
        delta = self.action_to_delta(context, obj, action)
        if obj_loc is None:
            obj_loc = obj.location
        loc = tuple(a + b for a, b in zip(obj_loc, delta))
        if not Board.is_in_bounds(loc):
            return None
        return loc

    def move(self, op, context, action):
        self.move_start(op, context, action)
        self.move_end(op, context)

    def move_start(self, op, context, action):
        obj = context.active_object
        obj.keyframe_insert(data_path='location')
        obj.keyframe_insert(data_path='rotation_euler')
        for obj_sel in context.selected_objects:
            obj_sel.select_set(obj_sel is obj)
        # make local for sync
        instr_export = bpy.context.scene.instr_export
        if ((len(bpy.context.scene["instr_export"]) == 0 or
                obj["value"] == obj["counter"])):
            instr_export = Board.loc_to_algebraic(context, obj.location)

        context.scene.rdc_game_current_frame += 1
        bpy.context.scene.frame_set(context.scene.rdc_game_current_frame)
        delta = self.action_to_delta(context, obj, action)
        bpy.ops.transform.translate(value=delta, orient_type='GLOBAL')

        instr_export += Board.loc_to_algebraic(context, obj.location)
        if bpy.context.scene.instr_import.upper() == instr_export.upper():
            # was other side
            instr_export = ""
        bpy.context.scene.instr_export = instr_export

    def move_end(self, op, context):
        obj = context.active_object
        context.scene.rdc_game_prev_active = obj.name
        self.capture(context, obj, op)
        obj.keyframe_insert(data_path='location')
        obj.keyframe_insert(data_path='rotation_euler')

    def is_on_path(self, obj, loc=None): # todo to algebraic encode
        if loc is None:
            loc = obj.location
        if not obj.animation_data.action:
            return False
        loc = tuple(map(round, loc))
        start_loc = tuple(map(round, obj["start_loc"]))
        curves = {}
        for curve in obj.animation_data.action.fcurves:
            if curve.data_path == "location":
                curves[curve.array_index] = curve.keyframe_points
        curves = [curves[index] for index in range(len(curves))]

        for index in reversed(range(len(curves[0]))):
            loc_keyed = tuple(round(keyframes[index].co[1]) for keyframes in curves)
            if all(a == b for a, b in zip(loc_keyed, loc)):
                return False
            if all(a == b for a, b in zip(loc_keyed, start_loc)):
                break
        return True

    def action_to_delta(self, context, obj, action):
        step = 1 * (-1 + bool(not Board.get_color(context, obj)) * 2)
        nd = divmod(self.move_names.index(action), 3)
        return tuple(comp * step for comp in (nd[1] - 1, nd[0] - 1, 0))

    def delta_to_action(self, context, obj, delta):
        step = 1 * (-1 + bool(Board.get_color(context, obj)) * 2)
        delta = tuple(comp // step + 1 for comp in delta)
        return self.move_names[delta[1] * 3 + delta[0]]

    def is_in_move_set(self, action):
        return action in self.move_set

    def capture(self, context, obj, op):
        collider = Board.intersect_board(context, obj)
        if collider is not None:
            collider.keyframe_insert(data_path='location',
                                     frame=bpy.context.scene.frame_current - 1)
            collider.location = (0, 9 if Board.get_color(context, collider) else -2,
                                 collider.location.z)
            collider.keyframe_insert(data_path='location')
            Board.intersect_out(context, collider)
            Board.end(context, obj, collider, op)


class King(Piece):
    move_set = Piece.move_names

    def poll_action(self, context, obj=None, obj_loc=None, action=None):
        if obj is None:
            obj = context.active_object

        loc = super().poll_action(context, obj, obj_loc, action)
        if loc is None:
            return False
        collider = Board.intersect_board(context, obj, loc)
        if collider is None:
            return True
        if Board.get_color(context, obj) == Board.get_color(context, collider):
            return False
        return not Board.get_type(collider) == "Rook"


class Rook(Piece):
    move_set = Piece.move_names_straight

    def poll_action(self, context, obj=None, obj_loc=None, action=None):
        loc = super().poll_action(context, obj, obj_loc, action)
        if loc is None:
            return False
        collider = Board.intersect_board(context, obj, loc)
        return collider is None


class Dice(Piece):
    move_set = Piece.move_names_straight
    rot_names = ('BACKWARD', 'FORWARD', 'RIGHT', 'LEFT')
    chirality = True
    value_matrix = tuple((n - (3 * bool(n >= 3))) * 2 + bool(n < 3)
            for n in (reversed(range(7)) if chirality else range(7)))

    up = mathutils.Vector((0, 0, 1))

    def init(self, obj):
        if not hasattr(obj, "value"):
            obj["value"] = self.rotation_to_value(obj.rotation_euler)
        if not hasattr(obj, "start"):
            obj["start"] = obj["value"]
            obj["counter"] = obj["value"]
            obj["start_loc"] = obj.location

    def reset(self, obj):
        obj["value"] = self.rotation_to_value(obj.rotation_euler)
        obj["start"] = obj["value"]
        obj["counter"] = obj["value"]
        obj["start_loc"] = obj.location

    def poll_action(self, context, obj=None, obj_loc=None, action=None):
        if obj is None:
            obj = context.active_object

        loc = super().poll_action(context, obj, obj_loc, action)
        if loc is None:
            return False
        collider = Board.intersect_board(context, obj, loc)
        if collider is None:
            return not (self is not None and not self.is_on_path(obj, loc))
        if Board.get_color(context, obj) == Board.get_color(context, collider):
            return False
        return obj["counter"] == 1 and not Board.get_type(collider) == "Rook"

    def move_start(self, op, context, action):
        super().move_start(op, context, action)

        obj = context.active_object
        step = 90
        nd = divmod(self.rot_names.index(action), 2)
        delta = (-1 + nd[1] * 2) * math.radians(step)
        bpy.ops.transform.rotate(value=delta * (-1 + bool(not Board.get_color(context, obj)) * 2),
                                 orient_axis=('X', 'Y')[nd[0]], orient_type='GLOBAL')
        obj["value"] = self.rotation_to_value(obj.rotation_euler)
        obj["counter"] -= 1

    def move_end(self, op, context):
        obj = context.active_object
        context.scene.rdc_game_prev_active = obj.name
        if obj["counter"] == 0:
            self.capture(context, obj, op)
            self.flip(context, obj)
            self.reset(obj)
        obj.keyframe_insert(data_path='location')
        obj.keyframe_insert(data_path='rotation_euler')

    def flip(self, context, obj):
        if bpy.context.scene.do_flip is False:
            return
        if obj["start"] == obj["value"]:
            bpy.ops.transform.rotate(value=math.radians(180) *
                                     (-1 + bool(not Board.get_color(context, obj)) * 2),
                                     orient_axis='X', orient_type='GLOBAL')

    def rotation_to_value(self, rotation):
        quat = rotation.to_quaternion()
        quat.invert()
        vec = self.up.copy()
        vec.rotate(quat)
        vec = tuple(round(comp) for comp in vec)
        index = sum(comp * (index + 1) + 1 for index, comp in enumerate(vec))
        return self.value_matrix[index]

    def value_to_rotation(self, value):
        index = self.value_matrix.index(value)
        if index > 3:
            index -= 1
        nd = divmod(index, 3)
        vec = mathutils.Vector()
        vec[nd[1]] = (-1 + nd[0] * 2)
        return vec.rotation_difference(self.up).to_euler()

    def randomize(self, obj):
        obj.rotation_euler = self.value_to_rotation(random.randint(1, 6))
        obj.rotation_euler.z = math.radians(90) * random.randint(1, 4)
        obj.keyframe_insert(data_path='location')
        obj.keyframe_insert(data_path='rotation_euler')
        self.init(obj)


class Queen(Dice):
    def init(self, obj):
        super().init(obj)
        obj["shared"] = False

    def reset(self, obj):
        super().reset(obj)
        obj["shared"] = False

    def poll_action(self, context, obj=None, obj_loc=None, action=None):
        if obj is None:
            obj = context.active_object

        loc = super(Dice, self).poll_action(context, obj, obj_loc, action)
        if loc is None:
            return False
        collider = Board.intersect_board(context, obj, loc)
        if collider is None:
            return not (self is not None and not self.is_on_path(obj, loc))
        if obj["shared"] and obj["counter"] > 1:
            return False
        if Board.get_color(context, obj) == Board.get_color(context, collider):
            return bool(obj["counter"] > 1)

        return not Board.get_type(collider) == "Rook"

    def move_end(self, op, context):
        obj = context.active_object
        collider = Board.intersect_board(context, obj)
        if collider is not None:
            obj["shared"] = True
        super().move_end(op, context)


def get_use_queen(self):
    return Board.setup[4] == "Q"

def set_use_queen(self, value):
    Board.setup = Board.setup[:4] + ("D", "Q")[value] + Board.setup[5:]


def get_fuzzy(context, name, parent=None):
    if parent is None:
        parent = context.scene.collection
    for coll in parent.children_recursive:
        if coll.name.startswith(name):
            return coll

    for obj in parent.all_objects:
        if obj.name.startswith(name):
            return obj


class VIEW3D_OT_rdc_set_view(Operator):
    bl_idname = "rdc_game.set_view"
    bl_label = "Set View"
    bl_description = "Set the viewport camera"

    action: EnumProperty(
        items=[
            ('BLACK', 'black', 'black'),
            ('WHITE', 'white', 'white'),
            ('SWITCH', 'switch', 'switch'),
            ('RANDOM', 'random', 'random'),
        ]
    )

    @classmethod
    def poll(cls, context):
        return (
            context.space_data is not None and
            context.space_data.type == 'VIEW_3D'
            )

    def execute(self, context):
        if context.mode != 'OBJECT':
            if bpy.ops.object.move_set.poll():
                bpy.ops.object.move_set(mode='OBJECT')

        region = context.space_data.region_3d
        x = math.radians(28)
        side_delta = 0
        if self.action != 'RANDOM':
            if self.action == 'SWITCH':
                view_euler = mathutils.Quaternion(region.view_rotation).to_euler()
                x = view_euler.x
                color = bool(abs(math.degrees(view_euler.z)) >= 90)
                side_delta = math.radians(min(max((
                                          math.degrees(view_euler.z) + 90) % 180 - 90, -45), 45))
            else:
                color = bool(self.action == 'WHITE')
        else:
            color = random.randint(0, 1)
            side_delta = math.radians(random.randint(-45, 45))

        region.view_location = (3.5, 3.5, 0)
        region.view_rotation = mathutils.Euler((min(x, math.radians(60)), 0,
                                                math.radians(180) * bool(not color) + side_delta)
                                                ).to_quaternion()
        region.view_distance = min(max(region.view_distance, 13), 22)
        region.is_perspective = True
        return {'FINISHED'}


classes = (
    RDC_OT_board,
    RDC_OT_board_history,
    RDC_OT_move_piece,
    VIEW3D_OT_rdc_set_view,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register():
    _register()
    Scene.rdc_game_current_frame = IntProperty(
            name='rdc_game_current_frame',
            description='Last frame with keys',
            subtype='TIME', min=0,
            )
    Scene.rdc_game_prev_active = StringProperty(
            name='rdc_game_prev_active',
            description='Name of the last active piece',
            )

def unregister():
    _unregister()
    del Scene.rdc_game_current_frame
    del Scene.rdc_game_prev_active
