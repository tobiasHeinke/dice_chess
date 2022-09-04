# SPDX-License-Identifier: GPL-3.0-or-later

import random

import bpy
from bpy.props import (
            BoolProperty,
            FloatProperty,
            FloatVectorProperty,
            StringProperty,
            )
from bpy.types import (
            Operator,
            Panel,
            Scene,
            )

from .main import get_use_queen, set_use_queen


class RDC_PT_settings(Panel):
    bl_idname = 'GAME_PT_SETTINGS_panel'
    bl_label = 'Dice Chess Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Game'

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.column().prop(context.scene, "seed")
        row.column().operator('rdc_game.gen_seed', text='', icon="FILE_REFRESH")

        layout.row().label(text='Variations:')
        row = layout.row()
        row.prop(context.scene, "do_flip", text="Flip")
        row = layout.row()
        row.prop(context.scene, "with_queen", text="With Queen")

        layout.row().separator()

        # release/scripts/startup/bl_ui/space_view3d
        layout.row().label(text='Ambiance:')
        row = layout.row()
        row.scale_y = 0.6
        row.template_icon_view(context.space_data.shading, "studio_light", scale_popup=3.0)
        row = layout.row()
        row.prop(context.space_data.shading, "studiolight_intensity", text="Dim")
        layout.row().label(text='Ground:')
        row = layout.row()
        row.prop(context.scene, 'background_color', text='')
        layout.row().label(text='Light:')
        row = layout.row()
        row.prop(context.scene, 'rdc_game_light_energy', text='')
        row = layout.row()
        row.prop(context.scene, 'rdc_game_light_color', text='')

        layout.row().separator()
        row = layout.row(align=True)
        row.operator('rdc_game.ui', text='Reapply Interface Changes', icon='WORKSPACE')


def get_background(self):
    mat = bpy.data.materials.get(bpy.context.scene.rdc_game_ground_ref)
    if mat is None:
        return (0, 0, 0, 0)
    node = mat.node_tree.nodes['Principled BSDF']
    if node is not None:
        value = list(node.inputs["Base Color"].default_value)
        value[3] = node.inputs["Alpha"].default_value
        return value

def set_background(self, value):
    mat = bpy.data.materials.get(bpy.context.scene.rdc_game_ground_ref)
    if mat is None:
        return None
    node = mat.node_tree.nodes['Principled BSDF']
    if node is not None:
        node.inputs["Base Color"].default_value = value
        if value[3] != 1:
            node.inputs["Alpha"].default_value = value[3]


def get_light_energy(self):
    light = bpy.data.lights.get(bpy.context.scene.rdc_game_light_ref)
    if light is None:
        return 0
    return light.energy

def set_light_energy(self, value):
    light = bpy.data.lights.get(bpy.context.scene.rdc_game_light_ref)
    if light is None:
        return None
    light.energy = value

def get_light_color(self):
    light = bpy.data.lights.get(bpy.context.scene.rdc_game_light_ref)
    if light is None:
        return (0, 0, 0)
    return light.color

def set_light_color(self, value):
    light = bpy.data.lights.get(bpy.context.scene.rdc_game_light_ref)
    if light is None:
        return None
    light.color = value


class RDC_OT_generate_seed(Operator):
    bl_idname = "rdc_game.gen_seed"
    bl_label = "Generate Random Seed"
    bl_description = "Generate random seed"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        context.scene.seed = str(random.randint(0, 1e8))
        return {'FINISHED'}


classes = (
    RDC_PT_settings,
    RDC_OT_generate_seed,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register():
    _register()
    Scene.seed = StringProperty(
        name='Seed',
        description='Start value for randomizer',
        )

    Scene.do_flip = BoolProperty(
        name='do_flip',
        default=False,
        )
    Scene.with_queen = BoolProperty(
        name='with_queen',
        description='(Effective after reset)',
        default=True,
        get=get_use_queen, set=set_use_queen
        )

    Scene.rdc_game_ground_ref = StringProperty()
    Scene.background_color = FloatVectorProperty(
        name='rdc_game_background_color',
        description='Background Color',
        subtype='COLOR', size=4, min=0, max=1,
        get=get_background, set=set_background,
        )

    Scene.rdc_game_light_ref = StringProperty()
    Scene.rdc_game_light_energy = FloatProperty(
        name='rdc_game_light_energy',
        description='Light Power',
        subtype="POWER", unit="POWER", step=100, min=0, max=10000,
        get=get_light_energy, set=set_light_energy,
        )
    Scene.rdc_game_light_color = FloatVectorProperty(
        name='rdc_game_light_color',
        description='Light Color',
        subtype='COLOR', size=3, min=0, max=1,
        get=get_light_color, set=set_light_color,
        )


def unregister():
    _unregister()
    del Scene.seed
    del Scene.do_flip
    del Scene.with_queen
