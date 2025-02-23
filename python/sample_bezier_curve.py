import bpy
import bezier
import numpy as np

if __name__ == "<run_path>":
    
    # Get the active curve object and its first spline
    curve_obj = bpy.context.active_object
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

        # Example usage
        t = 0.5  # Global parameter in [0, 1]
        point = evaluate_composite_curve(t)
        print(f"Point on the composite curve at t={t}: {point}")


        # # Define nodes for a 3D Bézier curve
        # nodes = np.asfortranarray([
        #     [0.0, 1.0, 2.0, 3.0],  
        #     [0.0, 2.0, 2.0, 0.0],  
        #     [0.0, 1.0, 3.0, 1.0]
        # ])

        # curve = bezier.Curve(nodes, degree=3)

        # # Evaluate the curve at a parameter t
        # t = 0.5
        # point = curve.evaluate(t)
        # print(f"Point on the curve at t={t}: {point.flatten()}")