# Create Armature
import bpy
from mathutils import Vector

armature = bpy.data.armatures.new('Armature')
armature_object=bpy.data.objects.new('Armature_object', armature)
armature_object.show_x_ray=True
armature.show_names=True
armature.draw_type = "STICK"

bpy.context.scene.objects.link(armature_object)
bpy.context.scene.objects.active = armature_object
bpy.context.scene.update()

bpy.ops.object.mode_set(mode='EDIT')

print("Creating bones")

for bone in self.bones:
    id = bone['id']
    pid = bone['parent_id']
    mtx = bone['matrix']

    joint = armature.edit_bones.new("bone_%03d" % id)
    joint.head = Vector( (0,0,0) )

    if pid != -1:
        joint.parent = armature.edit_bones[pid]
        joint.head = joint.parent.tail

    tail = Vector( (mtx[12], mtx[14], mtx[13]) )
    joint.tail = joint.head + tail

# Create Mesh

bm = bmesh.new()
mesh = bpy.data.meshes.new('Mesh')

for vertex in self.verts:
    pos = vertex['pos']
    x = pos[0]
    y = pos[1]
    z = pos[2]
    vert = bm.verts.new( (x, z, y) ) 

bm.verts.ensure_lookup_table()

for group in self.faces:
    for i in range(0, group['faceCount']):
        a = bm.verts[group['indices'][i * 3 + 0]['index']]
        b = bm.verts[group['indices'][i * 3 + 1]['index']]
        c = bm.verts[group['indices'][i * 3 + 2]['index']]
        face = bm.faces.new( (a, b, c) )
        face.material_index = group['materialIndex']
        # face.loop bmloop sequence to add uv


bm.to_mesh(mesh)
bm.free()

mesh_object = bpy.data.objects.new('Mesh_Object', mesh)

# For Vertex Weights, first we create a group for each bone
for i in range(0, len(self.bones)):
    mesh_object.vertex_groups.new("bone_%03d" % i)

#Loop over all of the vertices
for vertex in self.verts:
    index = vertex['index']
    indices = vertex['indices']
    weights = vertex['weights']
    mesh_object.vertex_groups[indices[0]].add([index], 1.0, "REPLACE")

bpy.ops.object.mode_set(mode='OBJECT')

mesh_object.parent = armature_object
modifier = mesh_object.modifiers.new(type='ARMATURE', name="Armature")
modifier.object = armature_object

bpy.context.scene.objects.link(mesh_object)
bpy.context.scene.objects.active = mesh_object