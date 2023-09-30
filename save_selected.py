import bpy
import mathutils
import math
from pxr import Usd, UsdGeom, Gf

stage = Usd.Stage.CreateNew("village5.usda")

for object in bpy.context.selected_objects:
    prim = stage.DefinePrim("/root/" + object.name.replace(".", "_"), "Xform")
    
    pos, rot, scale = (mathutils.Matrix.Rotation(-math.pi / 2.0, 4, 'X') @ object.matrix_basis @ mathutils.Matrix.Rotation(math.pi / 2.0, 4, 'X')).decompose()
        
    prim.SetInstanceable(True)
    prim = UsdGeom.Xformable(prim)
    prim.ClearXformOpOrder()
    prim.AddXformOp(UsdGeom.XformOp.TypeTranslate).Set(Gf.Vec3d(list(pos)))
    prim.AddXformOp(UsdGeom.XformOp.TypeOrient).Set(Gf.Quatd(*list(rot)))
    prim.AddXformOp(UsdGeom.XformOp.TypeScale).Set(Gf.Vec3d(list(scale)))
    
stage.GetRootLayer().Save()