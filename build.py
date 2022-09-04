# SPDX-License-Identifier: GPL-3.0-or-later

import math

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, Panel
import bmesh
import mathutils


class RDC_PT_build(Panel):
    bl_idname = 'GAME_PT_build'
    bl_label = 'Dice Chess Build Debug Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Game'

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        for name, icon in {
                'Ground': 'MESH_PLANE',
                'Board': 'MESH_GRID',
                'Light': 'LIGHT',
                'Dice': 'MESH_CUBE',
                'Queen': 'META_CUBE',
                'King': 'MESH_CONE',
                'Rook': 'MESH_CYLINDER',
                'Pieces': 'SCENE_DATA',
                'Scene': 'WORLD',
                }.items():
            layout.row().operator('rdc_game.builder', text=name, icon=icon).action = name.upper()


class RDC_OT_build(Operator):
    bl_idname = 'rdc_game.builder'
    bl_label = 'Game Builder'
    bl_description = 'Procedural game board and pieces'

    action: EnumProperty(
        items=[
            ('BOARD', 'board', 'board'),
            ('DICE', 'dice', 'dice'),
            ('GROUND', 'ground', 'ground'),
            ('KING', 'king', 'king'),
            ('LIGHT', 'light', 'light'),
            ('PIECES', 'pieces', 'pieces'),
            ('QUEEN', 'queen', 'queen'),
            ('SCENE', 'scene', 'scene'),
            ('ROOK', 'rook', 'rook'),
        ]
    )

    def execute(self, context):
        if self.action == 'SCENE':
            self.scene(context)
        elif self.action == 'PIECES':
            self.pieces(context)
        elif self.action == 'GROUND':
            self.ground(context)
        elif self.action == 'BOARD':
            self.board(context)
        elif self.action == 'LIGHT':
            self.light(context)
        elif self.action == 'DICE':
            self.dice(context, True)
        elif self.action == 'QUEEN':
            self.dice(context, True, True)
        elif self.action == 'KING':
            self.king(context, True)
        elif self.action == 'ROOK':
            self.rook(context, True)

        return {'FINISHED'}

    piece_names = {"King", "Queen", "Rook", "Dice"}
    theme = {
        "Ground": (0.026, 0.026, 0.026, 0.95),
        "Piece_Black": (0.015, 0.015, 0.015, 1),
        "Piece_White": (0.8, 0.8, 0.8, 1),
        "Board_Black": (0.042, 0.038, 0.037, 1),
        "Board_White": (0.204, 0.181, 0.144, 1),
        "Board_Nomination": (0.122, 0.123, 0.125, 1),
        "Light": (1, 0.98, 0.85),
    }

    def scene(self, context):
        wm = context.window_manager
        progress = 2
        self.ground(context)
        progress += 1
        wm.progress_update(progress)
        self.board(context)
        progress += 1
        wm.progress_update(progress)
        self.light(context)
        progress += 1
        wm.progress_update(progress)
        self.pieces(context)
        progress += 1
        wm.progress_update(progress)
        self.world(context)
        progress += 1
        wm.progress_update(progress)

    def pieces(self, context):
        coll_types = bpy.data.collections.new("Types")
        context.scene.collection.children.link(coll_types)

        eps = 0.01
        for color in range(2):
            coll_color = bpy.data.collections.new(("Black", "White")[color])
            coll_types.children.link(coll_color)
            for index, name in enumerate(self.piece_names):
                if name == 'Dice':
                   self.dice(context, color)
                elif name == 'Queen':
                    self.dice(context, color, True)
                elif name == 'King':
                   self.king(context, color)
                elif name == 'Rook':
                    self.rook(context, color)
                obj = context.active_object
                coll_color.objects.link(obj)
                obj.location = (index, 0, 0.35 + eps * bool(name == 'Queen'))
                obj.scale = (0.34, 0.34, 0.34)
                obj.hide_viewport = True


    def ground(self, context):
        bpy.ops.mesh.primitive_plane_add(size=10000, location = (0, 0, -1), calc_uvs=False)
        obj = context.active_object
        obj.name = "Ground"
        mat = self.new_material("Ground", specular=0, shadow=False)
        context.scene.rdc_game_ground_ref = mat.name
        obj.data.materials.append(mat)
        obj.hide_select = True

    def board(self, context):
        view_layer = context.view_layer
        bm = bmesh.new()
        md = bpy.data.meshes.new("Mesh")

        bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=8 / 2,
                        matrix=mathutils.Matrix.Translation((8 / 2 - 0.5, 8 / 2 - 0.5, 0.0)),
                        calc_uvs=False)
        bm.faces.ensure_lookup_table()
        for face in bm.faces:
            center = face.calc_center_median()
            face.material_index = int((round(center.x) % 2 == 0) ==
                                (round(center.y) % 2 == 0))

        bm.to_mesh(md)
        bm.free()
        obj_board = bpy.data.objects.new("Board", md)
        view_layer.active_layer_collection.collection.objects.link(obj_board)
        obj_board.data.materials.append(self.new_material("Board_White", specular=0.02,
                                                          shadow=False))
        obj_board.data.materials.append(self.new_material("Board_Black", specular=0.02,
                                                          shadow=False))
        obj_board.hide_select = True

        silver = self.new_material("Board_Nomination", shadow=False)
        for color in range(2):
            for axis in range(2):
                for square in range(8):
                    text = chr(square + 65) if axis else str(square + 1)
                    curve = bpy.data.curves.new(type="FONT", name="Font Curve " + text)
                    if axis:
                        curve.align_x = "CENTER"
                    else:
                        curve.align_y = "CENTER"
                    curve.body = text
                    curve.size = 0.4
                    obj = bpy.data.objects.new(name="Text " + text, object_data=curve)
                    if axis:
                        obj.location = (square, (-1, 8)[color], 0.0)
                    else:
                        obj.location = ((-1, 8)[color], square, 0.0)
                    if color:
                        obj.scale = (-1, -1, 0)
                    bpy.context.scene.collection.objects.link(obj)
                    obj.data.materials.append(silver)
                    obj.hide_select = True
                    obj.parent = obj_board


    def light(self, context):
        view_layer = bpy.context.view_layer
        data = bpy.data.lights.new(name="Light", type='POINT')
        context.scene.rdc_game_light_ref = data.name
        data.energy = 300
        data.color = self.theme["Light"]
        obj = bpy.data.objects.new(name="Light", object_data=data)
        view_layer.active_layer_collection.collection.objects.link(obj)
        obj.location = (4.5, 3.0, 5.0)
        obj.hide_select = True

    def dice(self, context, color, is_queen=False):
        def unit_to_value(vec):
            index = sum(comp * (index + 1) + 1 for index, comp in enumerate(vec))
            return value_matrix[index]

        view_layer = context.view_layer

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        md = bpy.data.meshes.new("Mesh")
        bm.to_mesh(md)
        bm.free()
        obj = bpy.data.objects.new(("Dice", "Queen")[is_queen], md)
        view_layer.active_layer_collection.collection.objects.link(obj)
        obj.select_set(True)
        view_layer.objects.active = obj


        # --- Create Faces

        cuts = tuple((0.3) * (n + 0.5 * bool(n == 0)) for n in range(0, 3))

        bpy.ops.object.mode_set(mode='EDIT')
        for side in range(3):
            bpy.ops.mesh.loopcut(number_cuts=len(cuts) * 2, object_index=0,
                                 edge_index=int(math.pow(side, 2)))

        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode='OBJECT')

        md = bpy.context.active_object.data
        bm = bmesh.new()
        bm.from_mesh(md)
        for vert in bm.verts:
            new_co = []
            for comp in vert.co:
                index = round(comp / 0.25)
                if abs(index) != 4:
                    comp = math.copysign(cuts[abs(index) - 1], index)
                new_co.append(comp)
            vert.co = new_co
        bm.to_mesh(md)
        bm.free()

        # --- Assign Material

        obj.data.materials.append(self.new_material(("Piece_Black", "Piece_White")[color],
                                                    specular=0.2))
        obj.data.materials.append(self.new_material(("Piece_Black", "Piece_White")
                                                    [bool(not color)], specular=0.2))

        pips = ((0, 0), (-1, -1), (1, 1), (-1, 1), (1, -1), (0, -1), (0, 1), (-1, 0), (1, 0))
        pips_queen = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        chirality = True
        # 2 * n + 1 if (n < 3) else -(7 - (2 * n + 1))
        value_matrix = tuple((n - (3 * bool(n >= 3))) * 2 + bool(n < 3)
                for n in (reversed(range(7)) if chirality else range(7)))

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        for face in bm.faces:
            center = face.calc_center_median()
            if (not all(abs(round(comp * 100)) in (0, 45, 100) for comp in center) and
                    (not is_queen or
                     not all(abs(round(comp * 100)) in (0, 80, 100) for comp in center))):
                continue
            value = unit_to_value(tuple(map(math.trunc, center)))

            uv = tuple(round(math.copysign(abs(comp) + 0.1, comp))
                       for comp in center if abs(comp) != 1)
            is_even = bool(value % 2 == 0)
            face.material_index = int(uv in (pips[is_even:value + is_even] if (not is_queen or
                        not any(abs(round(comp * 100)) == 80 for comp in center)) else
                        pips_queen))

        obj.data.update()
        bm.free()
        bpy.ops.object.mode_set(mode='OBJECT')

        self.new_bevel_modifier(context)
        bpy.ops.object.shade_smooth()

    def rook(self, context, color):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.97, depth=2,
                                            end_fill_type='TRIFAN', calc_uvs=False)
        obj = context.active_object
        obj.name = "Rook"
        self.new_bevel_modifier(context)
        bpy.ops.object.shade_smooth()
        obj.data.materials.append(self.new_material(("Piece_Black", "Piece_White")[color],
            specular=0.2))

    def king(self, context, color):
        view_layer = context.view_layer
        bm = bmesh.new()
        md = bpy.data.meshes.new("Mesh")
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True,
                        segments=8, radius1=0.92, radius2=0.1, depth=2.75,
                        matrix=mathutils.Matrix.Translation((0.0, 0.0, 0.75 / 2)), calc_uvs=False)
        bm.to_mesh(md)
        bm.free()
        obj = bpy.data.objects.new("King", md)
        view_layer.active_layer_collection.collection.objects.link(obj)
        obj.select_set(True)
        view_layer.objects.active = obj
        self.new_bevel_modifier(context)
        bpy.ops.object.shade_smooth()
        obj.data.materials.append(self.new_material(("Piece_Black", "Piece_White")[color],
                specular=0.2))

    def new_material(self, name, color=None, specular=None, shadow=True):
        mat = bpy.data.materials.get(name)
        if mat is not None:
            return mat

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        if mat.node_tree:
            links.clear()
            nodes.clear()

        output = nodes.new(type='ShaderNodeOutputMaterial')
        shader = nodes.new(type='ShaderNodeBsdfPrincipled')
        if color is None:
            color = self.theme[name]
        shader.inputs["Base Color"].default_value = color
        if color[3] != 1:
            shader.inputs["Alpha"].default_value = color[3]
            mat.blend_method = "BLEND"
        if specular is not None:
            shader.inputs["Specular"].default_value = specular
        links.new(shader.outputs[0], output.inputs[0])
        if not shadow:
            mat.shadow_method = "NONE"
        return mat

    @staticmethod
    def new_bevel_modifier(context):
        # bpy.ops.object.make_links_data(type='MODIFIERS')
        obj = context.active_object
        modifier = obj.modifiers.new(name='Bevel', type='BEVEL')
        modifier.width = 0.3 * 0.5
        modifier.segments = 4

    def world(self, context):
        color = list(self.theme["Ground"])
        color[3] = 0.99
        context.scene.world = self.new_world(context, "Game world", color=color)

    def new_world(self, context, name, color=None):
        world = bpy.data.worlds.get(name)
        if world is not None:
            return world

        world = bpy.data.worlds.new(name=name)
        world.use_nodes = True

        nodes = world.node_tree.nodes
        links = world.node_tree.links
        if world.node_tree:
            links.clear()
            nodes.clear()

        output = nodes.new(type="ShaderNodeOutputWorld")
        if color is None:
            color = self.theme[name]
        mix = nodes.new(type="ShaderNodeMixRGB")
        mix.inputs["Color2"].default_value = color
        links.new(mix.outputs[0], output.inputs[0])
        tex = nodes.new(type='ShaderNodeTexEnvironment')
        for sl in context.preferences.studio_lights:
            if sl.type == 'WORLD':
                tex.image = bpy.data.images.load(sl.path)
                break
        links.new(tex.outputs[0], mix.inputs[1])
        math_node = nodes.new(type='ShaderNodeMath')
        math_node.operation = 'MULTIPLY'
        math_node.inputs[1].default_value = color[3]
        links.new(math_node.outputs[0], mix.inputs[0])
        light_path = nodes.new(type="ShaderNodeLightPath")
        links.new(light_path.outputs["Is Camera Ray"], math_node.inputs[0])
        return world


classes = (
    RDC_OT_build,
    # RDC_PT_build,
)

_register, _unregister = bpy.utils.register_classes_factory(classes)

def register():
    _register()


def unregister():
    _unregister()


if __name__ == '__main__':
    register()
