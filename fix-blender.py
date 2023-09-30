# coding: utf-8
import MaterialX as mx
import sys

doc = mx.createDocument()
mx.readFromXmlFile(doc, sys.argv[1])

keep_inputs = set(('base', 'base_color', 'specular'))
replace_inputs = {'diffuse_roughness': 'specular_roughness'}

for node in doc.getNodes('standard_surface'):
    for node_input in node.getBindInputs():
        node_input_name = node_input.getName()
        if node_input_name not in keep_inputs and node_input_name not in replace_inputs:
            node.removeInput(node_input_name)

    for node_input in node.getBindInputs():
        node_input_name = node_input.getName()
        if node_input_name in replace_inputs:
            node_input.setName(replace_inputs[node_input_name])

print(mx.writeToXmlString(doc))
