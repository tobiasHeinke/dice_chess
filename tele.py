# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import (
            StringProperty,
            )
from bpy.types import (
            Operator,
            Panel,
            Scene,
            )
from .main import Board


class RDC_PT_tele(Panel):
    bl_idname = 'RDC_PT_tele'
    bl_label = 'Dice Chess Import/ Export'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Game'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        col = row.column()
        col.prop(context.scene, "instr_import", text='', icon="IMPORT")
        col = row.column()
        col.operator('rdc_game.paste', text='', icon="PASTEDOWN")
        row = layout.row(align=True)
        op = row.operator('rdc_game.board', text='Go', icon="PLAY") # "TRACKING"
        op.action = 'GO'
        row.enabled = Board.poll_instr(op, context)
        row = layout.row(align=True)
        col = row.column()
        col.prop(context.scene, "instr_export", text='', icon="EXPORT")
        col = row.column()
        col.operator('rdc_game.copy', text='', icon="COPYDOWN")


class RDC_OT_paste_import(Operator):
    bl_idname = "rdc_game.paste"
    bl_label = "Paste Import"
    bl_description = "Paste a move from the clipboard"

    @classmethod
    def poll(cls, context):
        instr_import = context.window_manager.clipboard
        return (instr_import and type(instr_import) is str)

    def execute(self, context):
        context.scene.instr_import = context.window_manager.clipboard
        return {'FINISHED'}


class RDC_OT_copy_export(Operator):
    bl_idname = "rdc_game.copy"
    bl_label = "Copy Export"
    bl_description = "Copy the last move to the clipboard"

    @classmethod
    def poll(cls, context):
        return context.scene.instr_export

    def execute(self, context):
        context.window_manager.clipboard = context.scene.instr_export
        return {'FINISHED'}


classes = (
    RDC_PT_tele,
    RDC_OT_paste_import,
    RDC_OT_copy_export,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register():
    _register()
    Scene.instr_import = StringProperty(
        name='instr_import',
        description='Import a move',
        maxlen=14,
        )
    Scene.instr_export = StringProperty(
        name='instr_export',
        description='Export a move',
        maxlen=14,
        )


def unregister():
    _unregister()
    del Scene.instr_import
    del Scene.instr_export
