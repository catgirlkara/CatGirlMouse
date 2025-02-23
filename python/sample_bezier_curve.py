import bpy
import bezier
import numpy as np


def create_visualization(verts, edges, faces):
    """ Create an object to visualize the closest points and a line connecting them. """
    try:
        mesh = bpy.data.meshes["TempMesh"]
        bpy.data.meshes.remove(mesh)
    except KeyError:
        pass

    mesh = bpy.data.meshes.new("TempMesh")
    obj = bpy.data.objects.new("TempMeshObj", mesh)
    bpy.context.collection.objects.link(obj)

    mesh.from_pydata(verts, edges, faces)
    mesh.update()
    
def get_curve_object(curveID):
    return bpy.data.objects.get(curveID)


def sample_blender_curve(curve_obj, t):
    spline_points = []
    for spline in curve_obj.data.splines:
        if spline.type == 'BEZIER' and len(spline.bezier_points) > len(spline_points):
            spline_points = spline.bezier_points

    # spline = curve_obj.data.splines[0]
    # for check_spline in curve_obj.data.splines:
    #     length = len(check_spline.bezier_points)
    #     if check_spline.type == 'BEZIER' and length > 1:
    #         spline = check_spline
    #         break


    # if spline.type == 'BEZIER':
        # spline_points = spline.bezier_points
    curve_segments = []
    curve_lengths = []
    total_length = 0
    
    for i in range(len(spline_points) - 1):
    #for i in range(1):
        spline_point_a = spline_points[i]
        spline_point_b = spline_points[i + 1]

        segment_nodes = []
        segment_nodes.append([spline_point_a.co.x, spline_point_a.handle_right.x, spline_point_b.handle_left.x, spline_point_b.co.x])
        segment_nodes.append([spline_point_a.co.y, spline_point_a.handle_right.y, spline_point_b.handle_left.y, spline_point_b.co.y])
        segment_nodes.append([spline_point_a.co.z, spline_point_a.handle_right.z, spline_point_b.handle_left.z, spline_point_b.co.z])

        curve_segment = bezier.Curve(np.asfortranarray(segment_nodes), degree=3)
        curve_segments.append(curve_segment)
        curve_length = curve_segment.length
        curve_lengths.append(curve_length)
        total_length += curve_length


    # Function to evaluate a point on the composite curve at parameter t
    def evaluate_composite_curve(t):
        assert 0.0 <= t <= 1.0, "Parameter t must be in [0, 1]"
        target_length = t * total_length
        accumulated_length = 0.0

        for curve, length in zip(curve_segments, curve_lengths):
            if accumulated_length + length >= target_length:
                local_t = (target_length - accumulated_length) / length
                point = curve.evaluate(local_t)
                return point.flatten()
            accumulated_length += length

        # If t == 1.0, return the end point of the last curve
        return curve_segments[len(curve_segments)-1].evaluate(1.0).flatten()

    point = evaluate_composite_curve(t)
    # print(f"Point on the composite curve at t={t}: {point}")

    # curve_obj = bpy.context.active_object
    return point



if __name__ == "<run_path>":
   
    curve = get_curve_object("GraphTest.004")
    
    blargPoints = []
    for vert in range(25):
        t = float(vert) / 24
        blargPoints.append(sample_blender_curve(curve, t) + curve.location)

    create_visualization(blargPoints, [], [])