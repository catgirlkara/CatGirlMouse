import bpy
import numpy as np
from scipy.optimize import minimize
import bpy
import bezier
import numpy as np
import mathutils
    
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

if __name__ == "<run_path>":
    
    curveA = get_curve_object("GraphTest.001")
    curveB = get_curve_object("GraphTest.009")

    curveA = get_curve_object("GraphTest.012")
    curveB = get_curve_object("GraphTest.020")

    # posA = sample_blender_curve(curveA, 0.5)
    # posB = sample_blender_curve(curveB, 0.5)

    # print(f"posA({posA}) :: posB({posB})")


        
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
    # Extract results
    t_min, s_min = result.x
    min_dist = np.sqrt(result.fun)

    print(f"Closest parameters: t = {t_min:.6f}, s = {s_min:.6f}")
    print(f"Minimum distance: {min_dist:.6f}")

    posA = sample_blender_curve(curveA, t_min) + [curveA.location.x, curveA.location.y, curveA.location.z]
    posB = sample_blender_curve(curveB, s_min) + [curveB.location.x, curveB.location.y, curveB.location.z]

    bpy.context.scene.cursor.location = posA + ((posB - posA) * 0.5)