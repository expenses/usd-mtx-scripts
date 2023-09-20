from pxr import Usd, UsdGeom
import bpy
import copy
from bpy_extras.io_utils import ImportHelper, ExportHelper
import os


def get_gltf_reference_path_for_prim(prim):
    stack = prim.GetPrimStack()
    # Not sure to do when this is > 1
    assert len(stack) == 1
    prim_spec = stack[0]
    references = prim_spec.referenceList.GetAppliedItems()
    assert len(references) == 1
    reference = references[0]
    return reference.assetPath


def load(filename):
    stage = Usd.Stage.Open(filename)

    gltf_path_to_collection = {}
    # prim_path_to_collection = {}
    prim_to_object = {}

    prototype_collection = bpy.data.collections.new("prototypes")
    prototype_collection.hide_viewport = True
    bpy.context.scene.collection.children.link(prototype_collection)

    cache = UsdGeom.XformCache()

    # Initial traversal for loading all the referenced glTFs
    for prim in stage.Traverse():
        direct_arcs = Usd.PrimCompositionQuery.GetDirectReferences(
            prim
        ).GetCompositionArcs()

        # The prim has an authored reference but it's not listed in the composition arcs,
        # meaning that it's a file with no associated usd handler.
        # Todo: this is hacky AF
        if len(direct_arcs) == 0 and prim.HasAuthoredReferences():
            filepath = get_gltf_reference_path_for_prim(prim)

            if filepath in gltf_path_to_collection:
                continue

            gltf_collection = bpy.data.collections.new(filepath)
            prototype_collection.children.link(gltf_collection)
            gltf_path_to_collection[filepath] = gltf_collection

            scene_path = prim.GetPath().AppendPath("Scenes").AppendPath("Scene")

            bpy.ops.import_scene.gltf(
                filepath=os.path.join(os.path.dirname(filename), filepath)
            )

            for object in bpy.context.selected_objects:
                # Todo: not sure whether to support referencing parts of a gltf scene or not.
                # if so, we need to create one collection for the whole gltf, and then a collection
                # per-component where each component is centered around the origin.
                """
                #object.location = (0, 0, 0)
                original_name = object.name.replace(".", "_")
                # Rename objects using the filename to prevent naming conflicts.
                object.name = filepath + "/" + original_name
                collection = bpy.data.collections.new(original_name)
                gltf_collection.children.link(collection)
                collection.objects.link(object)
                bpy.context.scene.collection.objects.unlink(object)
                # Usd doesn't like names that contain '.'s so we change them to underscores.
                # This is also what the guc plugin does.
                prim_path_to_collection[scene_path.AppendPath(original_name)] = collection
                """
                gltf_collection.objects.link(object)
                bpy.context.scene.collection.objects.unlink(object)

            # prim_path_to_collection[prim.GetPath()] = gltf_collection

    for prim in stage.Traverse():
        object = bpy.data.objects.new(str(prim.GetPath()), None)
        bpy.context.scene.collection.objects.link(object)

        object.matrix_basis = list(cache.GetLocalTransformation(prim)[0])
        # print(object.matrix_basis)
        # For y-up
        object.location = object.location.xzy
        object["usd_prim_path"] = str(prim.GetPath())
        object["usd_xform_matrix"] = copy.copy(object.matrix_basis)

        prim_to_object[prim] = object

        if prim.GetParent() and prim.GetParent() in prim_to_object:
            object.parent = prim_to_object[prim.GetParent()]

        if UsdGeom.Imageable(prim).GetVisibilityAttr().Get() == "invisible":
            object.hide_set(True)

        direct_arcs = Usd.PrimCompositionQuery.GetDirectReferences(
            prim
        ).GetCompositionArcs()

        if len(direct_arcs) == 0 and prim.HasAuthoredReferences():
            # Direct references, where a glTF file is being referenced
            filepath = get_gltf_reference_path_for_prim(prim)
            object.instance_type = "COLLECTION"
            object.instance_collection = gltf_path_to_collection[filepath]
        # See the above section about referencing parts of gltfs.
        """
        elif len(direct_arcs) > 0:
            # Indirect references, pointing to a direct reference.
            arc = direct_arcs[0]
            path = arc.GetTargetPrimPath()
            
            if not path in prim_path_to_collection:
                continue
                #assert False
            #assert path in prim_path_to_collection
            
            object.instance_type = "COLLECTION"
            object.instance_collection = prim_path_to_collection[path]
        """


""" 
class StoreCurrentTransforms(bpy.types.Operator):
    bl_idname = "object.store_current_transforms"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Store Current Transforms"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):        # execute() is called when running the operator.
        store_current_transforms()
        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class WriteOverride(bpy.types.Operator, ExportHelper):
    bl_idname = "object.write_override"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Write Override"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    filename_ext = ".usda"

    def execute(self, context):        # execute() is called when running the operator.
        write_override(self.filepath)

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.
"""


class OT_TestOpenFilebrowser(bpy.types.Operator, ImportHelper):
    bl_idname = "object.filebrowser_usd"
    bl_label = "Select root usd"

    filter_glob: bpy.props.StringProperty(default="*.usd*", options={"HIDDEN"})

    def execute(self, context):
        load(self.filepath)

        return {"FINISHED"}


class SaveLoadPanel(bpy.types.Panel):
    bl_label = "Save/Load"
    bl_category = "USD"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        # box.row().label(text=root_filename or "None")
        box.row().operator("object.filebrowser_usd")
        # box.row().operator("object.store_current_transforms")
        # box.row().operator("object.write_override")


# bpy.utils.register_class(Reload)
bpy.utils.register_class(OT_TestOpenFilebrowser)
# bpy.utils.register_class(StoreCurrentTransforms)
# bpy.utils.register_class(WriteOverride)
bpy.utils.register_class(SaveLoadPanel)