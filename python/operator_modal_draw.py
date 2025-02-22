import bpy

def curve_to_points_via_length(curve_obj_name, length):
	
	curve_obj = bpy.data.objects.get(curve_obj_name)
	"""
	Resamples the given curve object into points spaced by the specified segment length.

	Parameters:
		curve_obj (bpy.types.Object): The curve object to resample.
		segment_length (float): The desired length between resampled points.

	Returns:
		list of mathutils.Vector: A list of vectors representing the resampled points.
	"""
	# Add a Geometry Nodes modifier
	geo_mod = curve_obj.modifiers.new(name="ResampleCurve", type='NODES')

	group = geo_mod.node_group = bpy.data.node_groups.new('ResampleCurveGroup', 'GeometryNodeTree')

	group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
	input_node = group.nodes.new('NodeGroupInput')
	input_node.select = False
	input_node.location.x = -200 - input_node.width

	group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
	output_node = group.nodes.new('NodeGroupOutput')
	output_node.is_active_output = True
	output_node.select = False
	output_node.location.x = 200
	
	group.links.new(group.nodes["Group Input"].outputs[0], group.nodes["Group Output"].inputs[0])



	# Add a Resample Curve node
	resample_node = group.nodes.new(type='GeometryNodeCurveToPoints')
	resample_node.mode = 'LENGTH'  # Set mode to 'Length'
	resample_node.inputs['Length'].default_value = 0.01  # Set desired length between points


	group.links.new(input_node.outputs[0], resample_node.inputs[0])  # Connect 'Geometry' output to 'Curve' input
	group.links.new(resample_node.outputs[0], output_node.inputs[0])  # Connect 'Curve' output to 'Geometry' input

	# Apply the modifier to evaluate the geometry
	bpy.context.view_layer.update()

	# Access the evaluated mesh
	depsgraph = bpy.context.evaluated_depsgraph_get()
	eval_obj = curve_obj.evaluated_get(depsgraph)
	mesh = eval_obj.to_mesh()

	# Retrieve the sampled points
	sampled_points = [v.co for v in mesh.vertices]

	# Clean up
	eval_obj.to_mesh_clear()

	curve_obj.modifiers.remove(geo_mod)

	return sampled_points



if __name__ == "__main__":
	# Output the sampled points
	test_points = curve_to_points_via_length("GraphTest.004", 0.5)
	for point in test_points:
		print(point)
