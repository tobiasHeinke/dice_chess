# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator


class RDC_OT_key_override(Operator):
    bl_idname = "rdc_game.key_override"
    bl_label = "Key Override"
    bl_description = "Override key by doing nothing"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}


addon_keymaps = []

def register_keymap():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')

    move_names = (
        'BACKWARD_LEFT', 'BACKWARD', 'BACKWARD_RIGHT',
        'LEFT', 'NONE', 'RIGHT',
        'FORWARD_LEFT', 'FORWARD', 'FORWARD_RIGHT')
    keypads = ((
        'Z', 'X', 'C',
        'A', 'S', 'D',
        'Q', 'W', 'E'),(
        'B', 'N', 'M',
        'G', 'H', 'J',
        'T', 'Y', 'U'),(
        'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3',
        'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6',
        'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9')
        )

    keypad_margins = ((
        'COMMA',),(
        'NUMPAD_0', 'NUMPAD_PERIOD'))

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')

    kmi = km.keymap_items.new("rdc_game.set_view", "TAB", 'PRESS', ctrl=False, shift=False)
    kmi.properties.action = "SWITCH"
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("rdc_game.set_view", "SPACE", 'PRESS', ctrl=False, shift=False)
    kmi.properties.action = "SWITCH"
    addon_keymaps.append((km, kmi))

    for pad in reversed(keypads):
        for key, action in zip(pad, move_names):
            if action != "NONE":
                kmi = km.keymap_items.new('object.rdc_game_piece', key, 'PRESS',
                                          ctrl=False, shift=False)
                kmi.properties.action = action
            else:
                kmi = km.keymap_items.new("rdc_game.set_view", key, 'PRESS',
                                          ctrl=False, shift=False)
                kmi.properties.action = "SWITCH"

            addon_keymaps.append((km, kmi))

    for char in range(26):
        key = chr(char + 65)
        is_used = False
        for pad in keypads:
            if key in pad:
                is_used = True
                break
        if is_used:
            continue
        kmi = km.keymap_items.new(RDC_OT_key_override.bl_idname, key, 'PRESS',
                                  ctrl=False, shift=False)
        addon_keymaps.append((km, kmi))

    for pad in keypad_margins:
        for key in pad:
            kmi = km.keymap_items.new(RDC_OT_key_override.bl_idname, key, 'PRESS',
                                      ctrl=False, shift=False)
            addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("rdc_game.copy", "C", 'PRESS', ctrl=True, shift=False)
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new("rdc_game.paste", "V", 'PRESS', ctrl=True, shift=False)
    addon_keymaps.append((km, kmi))
    kmi = km.keymap_items.new('rdc_game.board', "RET", 'PRESS', ctrl=False, shift=False)
    kmi.properties.action = "GO"
    addon_keymaps.append((km, kmi))


classes = (
    RDC_OT_key_override,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)

def register():
    _register()

def unregister():
    _unregister()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
