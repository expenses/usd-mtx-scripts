import sys
import bpy
import mathutils
import math
from pxr import Usd, UsdGeom, Gf

filepath = sys.argv[4]
output = sys.argv[5]

bpy.ops.wm.open_mainfile(filepath=filepath)

def get_path(object):
    name = object.name.replace(".", "_")
    current_object = object
    while current_object.parent is not None:
        current_object = current_object.parent
        name = current_object.name.replace(".", "_") + "/" + name
    name = "/root/" + name
    return name

def collection_filepath(collection):
    return "assets/" + collection.library.name + ".glb"

def object_filepath(object):
    return "assets/" + object.name + ".glb"

stage = Usd.Stage.CreateNew(output)

export_collections = set()
export_objects = set()

for object in bpy.context.scene.collection.all_objects:
    prim = stage.DefinePrim(get_path(object), "Xform")

    if object.instance_collection is not None:
        prim.SetInstanceable(True)

        prim.GetReferences().AddReference(collection_filepath(object.instance_collection))
        export_collections.add(object.instance_collection)
    if object.data is not None:
        prim.SetInstanceable(True)
        prim.GetReferences().AddReference(object_filepath(object))
        export_objects.add(object)
    else:
        pos, rot, scale = (mathutils.Matrix.Rotation(-math.pi / 2.0, 4, 'X') @ object.matrix_basis @ mathutils.Matrix.Rotation(math.pi / 2.0, 4, 'X')).decompose()

        prim = UsdGeom.Xformable(prim)
        prim.ClearXformOpOrder()
        prim.AddXformOp(UsdGeom.XformOp.TypeTranslate).Set(Gf.Vec3d(list(pos)))
        prim.AddXformOp(UsdGeom.XformOp.TypeOrient).Set(Gf.Quatd(*list(rot)))
        prim.AddXformOp(UsdGeom.XformOp.TypeScale).Set(Gf.Vec3d(list(scale)))

for collection in export_collections:
    bpy.ops.object.select_all(action="DESELECT")
    for object in collection.all_objects:
        bpy.context.scene.collection.objects.link(object)
        object.select_set(True)
    bpy.ops.export_scene.gltf(filepath=collection_filepath(collection), use_selection=True, export_yup=True, export_apply=True)

for object in export_objects:
    bpy.ops.object.select_all(action="DESELECT")
    object.select_set(True)
    bpy.ops.export_scene.gltf(filepath=object_filepath(object), use_selection=True, export_yup=True, export_apply=True)

stage.GetRootLayer().Save()
