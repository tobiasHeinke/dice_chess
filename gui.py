# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator, Panel

from .main import Board, RDC_OT_board_history, RDC_OT_move_piece


class RDC_PT_main(Panel):
    bl_idname = 'RDC_PT_main'
    bl_label = 'Dice Chess'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Game'

    # use_pin = BoolProperty(
        # name = "Pin",
        # default = True,
        # description = "Pin"
        # )
    # use_pin = True
    @classmethod
    def poll(cls, context):
        return bool(
            context.object
            and context.object.mode == 'OBJECT'
        )

    def draw(self, context):
        layout = self.layout
        if not context.scene.rdc_game_is_setup:
            row = layout.row(align=True)
            row.scale_y = 3
            row.operator('rdc_game.new', text='New Game', icon='SCENE_DATA')
            return

        row = layout.row(align=True)
        row.label(text="Move Piece:") # dpad
        row = layout.row(align=True)
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='FL', icon='LOOP_BACK')
        op.action = 'FORWARD_LEFT'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='Forward', icon='SORT_DESC')
        op.action = 'FORWARD'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='FR', icon='LOOP_FORWARDS')
        op.action = 'FORWARD_RIGHT'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        row = layout.row(align=True)
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='Left', icon='BACK')
        op.action = 'LEFT'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        col = row.column()
        op = col.operator('rdc_game.set_view', text='Switch', icon='IMAGE_ALPHA')
        op.action = 'SWITCH'
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='Right', icon='FORWARD')
        op.action = 'RIGHT'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        row = layout.row(align=True)
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='BL', icon='TRACKING_BACKWARDS')
        op.action = 'BACKWARD_LEFT'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='Backward', icon='SORT_ASC')
        op.action = 'BACKWARD'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        col = row.column()
        op = col.operator('object.rdc_game_piece', text='BR', icon='ANIM_DATA')
        op.action = 'BACKWARD_RIGHT'
        col.enabled = RDC_OT_move_piece.poll_action(op, context)
        layout.row().separator()

        row = layout.row()
        col = row.column()
        op = col.operator('rdc_game.board_history', text='Undo', icon='TRIA_LEFT')
        op.action = 'UNDO'
        col.enabled = RDC_OT_board_history.poll_action(op, context)
        col = row.column()
        op = col.operator('rdc_game.board_history', text='Redo', icon='TRIA_RIGHT')
        op.action = 'REDO'
        col.enabled = RDC_OT_board_history.poll_action(op, context)

        row = layout.row()
        row.label(text="Value: [{0}] at {1} {2}"
                       .format(context.active_object.get("value", 0)
                               if context.active_object else 1,
                               Board.loc_to_algebraic(context),
                               ("■", "□")[Board.get_color(context)]))
        row = layout.row()
        moves = (context.active_object.get("counter", 0)
                               if context.active_object else 1,
                               context.active_object.get("start", 0)
                               if context.active_object else 1)
        row.label(text="Moves: {0}{1}{2}  {3} / {4}"
                       .format("█ " * moves[0],
                               "▒ " * (moves[1] - moves[0]),
                               "░ " * (6 - moves[1]),
                               moves[0], moves[1]))
        row = layout.row()
        row.label(text="Sum: {0} / {1}".format(*Board.sum_up(context)))

        layout.row().separator()
        row = layout.row(align=True)
        row.operator('rdc_game.board', text='Randomize', icon='FORCE_VORTEX').action = 'RANDOMIZE'
        row = layout.row()
        row.operator('rdc_game.board', text='Reset', icon='CANCEL').action = 'RESET'


class RDC_OT_ui_creator(Operator):
    bl_idname = 'rdc_game.ui'
    bl_label = 'Game UI'
    bl_description = 'Game UI creator'

    def execute(self, context):
        # bpy.ops.workspace.append_activate(idname="Layout")
        bpy.context.workspace.name = "Dice Chess"
        bpy.ops.workspace.reorder_to_front()
        # bpy.data.batch_remove(ids=[ws for ws in bpy.data.workspaces if ws.name != "Dice Chess"])

        context.space_data.show_region_toolbar = False
        context.space_data.show_region_tool_header = False
        context.space_data.show_region_header = False
        context.space_data.show_region_ui = True
        context.screen.show_statusbar = False
        for area in context.screen.areas:
            if area.type == "DOPESHEET_EDITOR":
                area.show_menus = False

        for prop in ("show_axis_x", "show_axis_y", "show_axis_z", "show_floor", "show_ortho_grid",
                        "show_cursor", "show_object_origins", "show_extras",
                        "show_text", "show_relationship_lines"):
            setattr(context.space_data.overlay, prop, False)

        context.scene.render.engine = "BLENDER_EEVEE"
        context.space_data.shading.type = "RENDERED"
        context.space_data.shading.use_scene_world = False
        context.space_data.shading.use_scene_world_render = False
        context.space_data.shading.studiolight_background_alpha = 1

        for area in reversed(context.screen.areas):
            if (area.type != "VIEW_3D" and
                    (area.type != "DOPESHEET_EDITOR" or area.spaces[0].mode != 'TIMELINE')):
                with context.temp_override(area=area):
                    if bpy.ops.screen.area_close.poll():
                        bpy.ops.screen.area_close()

        for area in context.screen.areas:
            if area.type == "DOPESHEET_EDITOR":
                break
        else:
            bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.08)
            area = context.screen.areas[-1]
            with bpy.context.temp_override(area=area):
                bpy.ops.screen.space_type_set_or_cycle(space_type='DOPESHEET_EDITOR')
                area.spaces[0].mode = 'TIMELINE'
                area.spaces[0].show_region_ui = False
                area.show_menus = False

        return {'FINISHED'}


classes = (
    RDC_PT_main,
    RDC_OT_ui_creator,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register():
    _register()

def unregister():
    _unregister()
