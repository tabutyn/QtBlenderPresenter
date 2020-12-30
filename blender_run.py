import bpy
import bpy.ops as O
import sys
import json
from json import JSONDecodeError
C = bpy.context


print("hello")
blender_to_qt = sys.argv[4]
blender_to_qt_dict = {}
qt_to_blender = sys.argv[5]
scene = C.scene
blender_frame = 0
qt_frame = 0

scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 400
scene.render.resolution_y = 400
scene.eevee.taa_render_samples = 1
while True:
    while qt_frame == blender_frame:
        with open(f'{qt_to_blender}', 'r') as f:
            try:
                qt_to_blender_dict = json.load(f)
            except JSONDecodeError:
                print("json miss")

        qt_frame = int(qt_to_blender_dict['qt_frame'])
    stash_location = bpy.data.objects['Camera'].location.copy()
    bpy.data.objects['Camera'].location.x += 4.0
    scene.render.filepath = sys.argv[6] + '_0.png'
    O.render.render(write_still=True)
    bpy.data.objects['Camera'].location = stash_location
    bpy.data.objects['Camera'].location.y += 4.0
    scene.render.filepath = sys.argv[6] + '_1.png'
    O.render.render(write_still=True)
    bpy.data.objects['Camera'].location = stash_location
    bpy.data.objects['Camera'].location.z += 4.0
    scene.render.filepath = sys.argv[6] + '_2.png'
    O.render.render(write_still=True)
    bpy.data.objects['Camera'].location = stash_location
    bpy.data.objects['Cube']

    blender_frame = qt_frame
    print(f"blender_frame: {blender_frame}")
    blender_to_qt_dict.update({'blender_frame': blender_frame})
    with open(f'{blender_to_qt}', 'w+') as f:
        json.dump(blender_to_qt_dict, f)

