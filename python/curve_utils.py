import bpy
import numpy as np
from scipy.optimize import minimize
import bezier
import mathutils
import time
    
def sample_blender_curve(curve_obj, t):
    spline = curve_obj.data.splines[0]

    if spline.type == 'BEZIER':
        spline_points = spline.bezier_points
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
            return curve_segments[-1].evaluate(1.0).flatten()

        point = evaluate_composite_curve(t)
        # print(f"Point on the composite curve at t={t}: {point}")

        # curve_obj = bpy.context.active_object
        return point

def get_curve_object(curveID):
    return bpy.data.objects.get(curveID)

def get_curve_intersection(curveA, curveB):
    # Initial guess for (t, s)
    t_init, s_init = 0.5, 0.5

    def distance_squared(params):
        """ Function to minimize: Squared Euclidean distance between C1(t) and C2(s) """
        t, s = params
        posA = sample_blender_curve(curveA, t) + [curveA.location.x, curveA.location.y, curveA.location.z]
        posB = sample_blender_curve(curveB, s) + [curveB.location.x, curveB.location.y, curveB.location.z]
        return np.sum((posA - posB)**2)

    # Minimize distance_squared with constraints on t and s
    result = minimize(distance_squared, x0=[t_init, s_init], bounds=[(0, 1), (0, 1)])

    print(f"result.x")

    return result

def lerp(a, b, t: float):
    """Linear interpolate on the scale given by a to b, using t as the point on that scale.
    Examples
    --------
        50 == lerp(0, 100, 0.5)
        4.2 == lerp(1, 5, 0.8)
    """
    return (1 - t) * a + t * b

def inverse_lerp(a, b, v) -> float:
    """Inverse Linar Interpolation, get the fraction between a and b on which v resides.
    Examples
    --------
        0.5 == inv_lerp(0, 100, 50)
        0.8 == inv_lerp(1, 5, 4.2)
    """
    if(a > b):
        x = b
        b = a
        a = x
    return (v - a) / (b - a)

def create_visualization(points):
    """ Create an object to visualize the closest points and a line connecting them. """
    try:
        mesh = bpy.data.meshes["TempMesh"]
        bpy.data.meshes.remove(mesh)
    except KeyError:
        pass

    mesh = bpy.data.meshes.new("TempMesh")
    obj = bpy.data.objects.new("TempMeshObj", mesh)
    bpy.context.collection.objects.link(obj)

    # Create mesh data
    verts = points
    edges = []
    faces = []

    mesh.from_pydata(verts, edges, faces)
    mesh.update()

if __name__ == "<run_path>":
    
    # curveA = get_curve_object("GraphTest.012")
    # curveB = get_curve_object("GraphTest.021")

    # intersection = get_curve_intersection(curveA, curveB)
    
    # t_min, s_min = intersection.x
    # # min_dist = np.sqrt(intersection.fun)

    # # print(f"Closest parameters: t = {t_min:.6f}, s = {s_min:.6f}")
    # # print(f"Minimum distance: {min_dist:.6f}")

    # posA = sample_blender_curve(curveA, t_min) + [curveA.location.x, curveA.location.y, curveA.location.z]
    # posB = sample_blender_curve(curveB, s_min) + [curveB.location.x, curveB.location.y, curveB.location.z]

    # # bpy.context.scene.cursor.location = posA + ((posB - posA) * 0.5)


    blargPoints = []

    leftCurve = get_curve_object("GraphTest.012")
    rightCurve = get_curve_object("GraphTest.001")
    topCurve = get_curve_object("GraphTest.021")
    bottomCurve = get_curve_object("GraphTest.009")

    botLeftIntersection = get_curve_intersection(leftCurve, bottomCurve)
    botRightIntersection = get_curve_intersection(rightCurve, bottomCurve)
    topRightIntersection = get_curve_intersection(rightCurve, topCurve)
    topLeftIntersection = get_curve_intersection(leftCurve, topCurve)


    leftStartT, bottomStartT = botLeftIntersection.x
    rightStartT, bottomEndT = botRightIntersection.x
    rightEndT, topEndT = topRightIntersection.x
    leftEndT, topStartT = topLeftIntersection.x
    
    # bpy.context.scene.cursor.location = blargPoints[0]

    # blargPoints.append(sample_blender_curve(bottomCurve, lerp(bottomStartT, bottomEndT, .5)) + bottomCurve.location)
    # blargPoints.append(sample_blender_curve(topCurve, lerp(topStartT, topEndT, .5)) + topCurve.location)
    # blargPoints.append(sample_blender_curve(leftCurve, lerp(leftStartT, leftEndT, .5)) + leftCurve.location)
    # blargPoints.append(sample_blender_curve(rightCurve, lerp(rightStartT, rightEndT, .5)) + rightCurve.location)
    


    for xVert in range(15):
        xT = float(xVert) / 14
        bottomT = lerp(bottomStartT, bottomEndT, xT)
        bottomPosition = sample_blender_curve(bottomCurve, bottomT) + bottomCurve.location
        topT = lerp(topStartT, topEndT, xT)
        topPosition = sample_blender_curve(topCurve, topT) + topCurve.location

        for yVert in range(15):
            yT = float(yVert) / 14
            leftT = lerp(leftStartT, leftEndT, yT)
            leftPosition = sample_blender_curve(leftCurve, leftT) + leftCurve.location
            rightT = lerp(rightStartT, rightEndT, yT)
            rightPosition = sample_blender_curve(rightCurve, rightT) + rightCurve.location

            verticalPosition = lerp(leftPosition, rightPosition, xT)
            horizontalPosition = lerp(bottomPosition, topPosition, yT)

            blargPoints.append(verticalPosition)
            blargPoints.append(horizontalPosition)
            # blargPoints.append(horizontalPosition + ((verticalPosition - horizontalPosition) * 0.5))

    create_visualization(blargPoints)






            