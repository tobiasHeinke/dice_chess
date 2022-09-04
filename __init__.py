# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Rolling Dice Chess",
    "author": "Tobias Heinke",
    "location": "3D Viewport > Sidebar > Game > Dice Chess",
    "version": (0, 0, 1),
    "blender": (3, 0, 0),
    "description": "Rolling Dice Chess Game",
    "doc_url": "https://github.com/tobiasHeinke/dice_chess/wiki",
    "tracker_url": "https://github.com/tobiasHeinke/dice_chess/issues",
    "category": "3D View"
}


if "bpy" in locals():
    import importlib
    importlib.reload(main)
    importlib.reload(gui)
    importlib.reload(keymaps)
    importlib.reload(tele)
    importlib.reload(settings)
    importlib.reload(build)
else:
    from . import main
    from . import gui
    from . import keymaps
    from . import tele
    from . import settings
    from . import build


import bpy
from bpy.props import BoolProperty
from bpy.types import Operator, Scene


class RDC_OT_new(Operator):
    bl_idname = 'rdc_game.new'
    bl_label = 'New Game'
    bl_description = 'Create and init new game scene'

    def execute(self, context):
        wm = context.window_manager
        progress = 0
        wm.progress_begin(progress, 10)
        progress += 1
        wm.progress_update(progress)
        bpy.ops.scene.new(type='NEW')
        bpy.context.scene.name = "Dice Chess"
        progress += 1
        wm.progress_update(progress)
        bpy.ops.rdc_game.builder(action='SCENE')
        progress += 4
        bpy.ops.rdc_game.board(action='RESET')
        progress += 1
        wm.progress_update(progress)
        bpy.ops.rdc_game.ui()
        progress += 1
        wm.progress_update(progress)
        keymaps.register_keymap()
        progress += 1
        wm.progress_update(progress)
        bpy.ops.rdc_game.set_view(action='RANDOM')
        context.scene.rdc_game_is_setup = True
        wm.progress_end()
        return {'FINISHED'}


classes = (
    RDC_OT_new,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)

def register():
    _register()
    main.register()
    gui.register()
    keymaps.register()
    tele.register()
    settings.register()
    build.register()

    Scene.rdc_game_is_setup = BoolProperty(
        name='is_setup',
        default=False
        )


def unregister():
    _unregister()
    main.unregister()
    gui.unregister()
    keymaps.unregister()
    tele.unregister()
    settings.unregister()
    build.unregister()

    del Scene.rdc_game_is_setup

if __name__ == '__main__':
    register()
