import bpy
import bmesh
import math

bl_info = {
    'name': 'Proportional Subdivide',
    'description': 'Divide edges into specific proportions.',
    'author': 'Manuel Caldeira',
    'version': (1, 0),
    'blender': (2, 79, 0),
    'location': 'View3D > Tool Shelf > Tools > Mesh Tools',
    'warning': '',
    'category': 'Mesh',
}


class ProportionItem(bpy.types.PropertyGroup):
    #value = bpy.props.FloatProperty(min=0.0, default=1.0, precision=6, subtype='FACTOR', unit='LENGTH')
    value = bpy.props.StringProperty(name='', description='', default='a')


class ProportionSettings(bpy.types.PropertyGroup):
    props = bpy.props.CollectionProperty(type=ProportionItem)
    active_index = bpy.props.IntProperty()
    
    reverse = bpy.props.BoolProperty(name='Reverse', description='Reverse the direction the proportions are applied.', default=False)


class TOOLS_UL_props(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text='', icon='EDGESEL')
            row.prop(item, 'value', emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text='', icon_value=icon)


modify_type_items = {
    'ADD':    {'name': '', 'description': 'Add another segment.',
               'icon': 'ZOOMIN',    'number': 0},
    'REMOVE': {'name': '', 'description': 'Remove selected segment.',
               'icon': 'ZOOMOUT',   'number': 1},
    'CLEAR':  {'name': '', 'description': 'Remove all segments.',
               'icon': 'X',         'number': 2},
    'UP':     {'name': '', 'description': 'Move selected segment up.',
               'icon': 'TRIA_UP',   'number': 3},
    'DOWN':   {'name': '', 'description': 'Move selected segment down.',
               'icon': 'TRIA_DOWN', 'number': 4},
}


class ModifyProportion(bpy.types.Operator):
    bl_idname = 'mesh.subdivide_proportional_modify'
    bl_label = ''
    bl_options = {'UNDO'}

    type = bpy.props.EnumProperty(
        items=set((key, *val.values()) for key, val in modify_type_items.items()),
        default=None,
    )
    
    def invoke(self, context, event):
        ts = context.scene.subdivide_proportional_settings
        if self.type == 'ADD':
            ts.props.add()
            if ts.active_index < 0:
                ts.active_index = 0
            ts.props.move(len(ts.props) - 1, ts.active_index)
        elif self.type == 'REMOVE':
            ts.props.remove(ts.active_index)
            if ts.active_index >= len(ts.props):
                ts.active_index = len(ts.props) - 1
        elif self.type == 'CLEAR':
            ts.props.clear()
        else:
            if self.type == 'UP':
                new_index = (ts.active_index - 1) % len(ts.props)
            elif self.type == 'DOWN':
                new_index = (ts.active_index + 1) % len(ts.props)
            ts.props.move(ts.active_index, new_index)
            ts.active_index = new_index
        return {'FINISHED'}


class SubdivideProportional(bpy.types.Operator):
    bl_idname = 'mesh.subdivide_proportional'
    bl_label = 'Proportional Subdivide'
    bl_description = 'Subdivide selected edges by the common factor \'a\'.'
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        ts = context.scene.subdivide_proportional_settings
        return len(ts.props) > 0

    def invoke(self, context, event):
        return self.execute(context)
    
    def execute(self, context):
        ts = context.scene.subdivide_proportional_settings
        
        # update mesh data (..?)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj = context.active_object.data
        bpy.ops.object.mode_set(mode='EDIT')
        
        msh = bmesh.from_edit_mesh(obj)
        selectedEdges = list(e for e in msh.edges if e.select)
        
        for edge in selectedEdges:
            vert1, vert2 = reversed(edge.verts) if ts.reverse else edge.verts
            functions = list(s.value for s in ts.props)
            proportions = SubdivideProportional.get_proportions(functions)
            while proportions:
                prop = proportions[0]
                psum = sum(proportions)
                fact = 1 - (prop / psum)
                if fact > 0:
                    edge, vert = bmesh.utils.edge_split(edge, vert2, fact)
                    vert.select = True
                del proportions[0]
            
        bmesh.update_edit_mesh(obj, True)
        
        return {'FINISHED'}
    
    # TODO perhaps a nicer way of entering proportions ?
    @staticmethod
    def get_proportions(functions, length=1, var_name='a'):
        math_globals = dict((name, getattr(math, name)) for name in dir(math) if not name.startswith('_'))
        
        return list(eval(f, math_globals, {var_name: 1}) for f in functions)
        
        # TODO may be useful for ui purposes?
        normal_sum = sum(eval(f, math_globals, {var_name: 1}) for f in functions)
        
        ratio = length / normal_sum
        
        return list(eval(f, math_globals, {var_name: ratio}) for f in functions)


def render_panel(self, context):
    ts = context.scene.subdivide_proportional_settings
    layout = self.layout
    
    col = layout.column(align=True)
    col.label(text='Proportional Subdivide:')
    
    row = col.row()
    sub = row.column()
    sub.template_list('TOOLS_UL_props', '', ts, 'props', ts, 'active_index', rows=3, maxrows=5)
    
    sub = row.column(align=True)
    sub.operator('mesh.subdivide_proportional_modify',
                    text=modify_type_items['ADD']['name'],
                    icon=modify_type_items['ADD']['icon']).type = 'ADD'
    if len(ts.props) > 0:
        sub.operator('mesh.subdivide_proportional_modify',
                    text=modify_type_items['REMOVE']['name'],
                    icon=modify_type_items['REMOVE']['icon']).type = 'REMOVE'
        sub.operator('mesh.subdivide_proportional_modify',
                    text=modify_type_items['CLEAR']['name'],
                    icon=modify_type_items['CLEAR']['icon']).type = 'CLEAR'
    if len(ts.props) > 1:
        sub.separator()
        sub.operator('mesh.subdivide_proportional_modify',
                    text=modify_type_items['UP']['name'],
                    icon=modify_type_items['UP']['icon']).type = 'UP'
        sub.operator('mesh.subdivide_proportional_modify',
                    text=modify_type_items['DOWN']['name'],
                    icon=modify_type_items['DOWN']['icon']).type = 'DOWN'
    
    col.separator()
    spl = col.split(percentage=0.7, align=True)
    spl.operator('mesh.subdivide_proportional')
    spl.prop(ts, 'reverse', toggle=True)


def register():
    bpy.utils.register_class(TOOLS_UL_props)
    
    bpy.utils.register_class(ProportionItem)
    bpy.utils.register_class(ProportionSettings)
    
    bpy.types.Scene.subdivide_proportional_settings = bpy.props.PointerProperty(type=ProportionSettings)
    
    bpy.utils.register_class(ModifyProportion)
    bpy.utils.register_class(SubdivideProportional)
    
    bpy.types.VIEW3D_PT_tools_meshedit.append(render_panel)


def unregister():    
    bpy.utils.unregister_class(TOOLS_UL_props)

    bpy.utils.unregister_class(ProportionItem)
    bpy.utils.unregister_class(ProportionSettings)
    
    del bpy.types.Scene.subdivide_proportional_settings
    
    bpy.utils.unregister_class(ModifyProportion)
    bpy.utils.unregister_class(SubdivideProportional)
    
    bpy.types.VIEW3D_PT_tools_meshedit.remove(render_panel)
