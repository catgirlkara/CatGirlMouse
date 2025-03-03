import bpy
import numpy as np
from scipy.optimize import minimize
import bezier
import mathutils
import time

from collections.abc import Awaitable, Callable, Iterable, Iterator, MutableSet, Reversible, Set as AbstractSet, Sized

def transform_points_from_BY_to_AZ(B : np.ndarray, Y : np.ndarray, A : np.ndarray, Z : np.ndarray, points : Iterable[np.ndarray]):
    # Direction vectors
    v1 = Y - B
    v2 = Z - A

    # Lengths of the segments
    L1 = np.linalg.norm(v1)
    L2 = np.linalg.norm(v2)

    # Unit vectors
    u1 = v1 / L1
    u2 = v2 / L2

    # Compute the cross product and dot product
    cross_prod = np.cross(u1, u2)
    dot_prod = np.dot(u1, u2)

    # Skew-symmetric cross-product matrix
    K = np.array([
        [0, -cross_prod[2], cross_prod[1]],
        [cross_prod[2], 0, -cross_prod[0]],
        [-cross_prod[1], cross_prod[0], 0]
    ])

    # Rotation matrix using Rodrigues' rotation formula
    I = np.eye(3)
    R = I + K + K @ K * ((1 - dot_prod) / (np.linalg.norm(cross_prod) ** 2))


    # Scaling factor
    s = L2 / L1

    # Combined rotation and scaling matrix
    M = s * R

    # Affine transformation matrix in homogeneous coordinates
    affine_matrix = np.eye(4)
    affine_matrix[:3, :3] = M
    affine_matrix[:3, 3] = A - M @ B

    transformed_points = []
    for P in points:
        # Convert P to homogeneous coordinates
        P_homogeneous = np.append(P, 1)

        # Apply the affine transformation
        P_transformed_homogeneous = affine_matrix @ P_homogeneous

        # Convert back to Cartesian coordinates
        P_transformed = P_transformed_homogeneous[:3]

        transformed_points.append(P_transformed)

    return transformed_points
    

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

    return result

def loop(x: float, min:float=0, max:float=1):
	LocalMax = (max - min)
	return (min + ((x) % LocalMax + LocalMax) % LocalMax)

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
    bpy.context.view_layer.objects.active = mesh
    # bpy.ops.mesh.remove_doubles(5)
    


def get_curve_section_points(leftCurve, rightCurve, topCurve, bottomCurve):
    sectionPoints = []

    botLeftIntersection = get_curve_intersection(leftCurve, bottomCurve)
    botRightIntersection = get_curve_intersection(rightCurve, bottomCurve)
    topRightIntersection = get_curve_intersection(rightCurve, topCurve)
    topLeftIntersection = get_curve_intersection(leftCurve, topCurve)


    leftStartT, bottomStartT = botLeftIntersection.x
    rightStartT, bottomEndT = botRightIntersection.x
    rightEndT, topEndT = topRightIntersection.x
    leftEndT, topStartT = topLeftIntersection.x

    # if leftStartT > leftEndT:
    #     leftEndT += 1
    # if bottomStartT > bottomEndT:
    #     bottomEndT += 1
    # if rightStartT > rightEndT:
    #     rightEndT += 1
    # if topStartT > topEndT:
    #     topEndT += 1
    
    # bpy.context.scene.cursor.location = blargPoints[0]

    # blargPoints.append(sample_blender_curve(bottomCurve, lerp(bottomStartT, bottomEndT, .5)) + bottomCurve.location)
    # blargPoints.append(sample_blender_curve(topCurve, lerp(topStartT, topEndT, .5)) + topCurve.location)
    # blargPoints.append(sample_blender_curve(leftCurve, lerp(leftStartT, leftEndT, .5)) + leftCurve.location)
    # blargPoints.append(sample_blender_curve(rightCurve, lerp(rightStartT, rightEndT, .5)) + rightCurve.location)
    
    for xVert in range(15):
        xT = float(xVert) / 14
        bottomT = lerp(bottomStartT, bottomEndT, xT)
        bottomPosition = np.array(sample_blender_curve(bottomCurve, bottomT) + bottomCurve.location)
        topT = lerp(topStartT, topEndT, xT)
        topPosition = np.array(sample_blender_curve(topCurve, topT) + topCurve.location)

        verticalVerts = []
        for yVert in range(15):
            yT = float(yVert) / 14
            verticalPosition = None
            
            leftT = lerp(leftStartT, leftEndT, yT)
            leftPosition = np.array(sample_blender_curve(leftCurve, leftT) + leftCurve.location)
            rightT = lerp(rightStartT, rightEndT, yT)
            rightPosition = np.array(sample_blender_curve(rightCurve, rightT) + rightCurve.location)

            verticalPosition = lerp(leftPosition, rightPosition, xT)

            verticalVerts.append(verticalPosition)

        B, *_, Y = verticalVerts
        A = bottomPosition
        Z = topPosition
        
        transformedVerts = transform_points_from_BY_to_AZ(B, Y, A, Z, verticalVerts)
        for vert in transformedVerts:
            sectionPoints.append(vert)



    # for yVert in range(15):
    #     yT = float(yVert) / 14
    #     leftT = lerp(leftStartT, leftEndT, yT)
    #     leftPosition = np.array(sample_blender_curve(leftCurve, leftT) + leftCurve.location)
    #     rightT = lerp(rightStartT, rightEndT, yT)
    #     rightPosition = np.array(sample_blender_curve(rightCurve, rightT) + rightCurve.location)
        
    #     horizontalVerts = []
    #     for xVert in range(15):
    #         xT = float(xVert) / 14
    #         bottomT = lerp(bottomStartT, bottomEndT, xT)
    #         bottomPosition = np.array(sample_blender_curve(bottomCurve, bottomT) + bottomCurve.location)
    #         topT = lerp(topStartT, topEndT, xT)
    #         topPosition = np.array(sample_blender_curve(topCurve, topT) + topCurve.location)


    #         horizontalPosition = lerp(bottomPosition, topPosition, yT)

    #         horizontalVerts.append(horizontalPosition)

    #     B, *_, Y = horizontalVerts
    #     A = leftPosition
    #     Z = rightPosition
        
    #     transformedVerts = transform_points_from_BY_to_AZ(B, Y, A, Z, horizontalVerts)
    #     # for vert in transformedVerts:
    #     #     sectionPoints.append(vert)

    return sectionPoints

def get_15x15_faces(blargPoints):
    # Number of vertices along one dimension
    grid_size = 15

    # Initialize the list to store quads
    quads = []

    # Iterate over each cell in the grid
    for i in range(grid_size - 1):
        for j in range(grid_size - 1):
            # Calculate the indices of the four corners of the current quad
            top_left = i * grid_size + j
            top_right = top_left + 1
            bottom_left = top_left + grid_size
            bottom_right = bottom_left + 1

            # Append the quad as a tuple of indices
            top_left += len(blargPoints) - (15*15)
            top_right += len(blargPoints) - (15*15)
            bottom_right += len(blargPoints) - (15*15)
            bottom_left += len(blargPoints) - (15*15)
            quads.append((top_left, top_right, bottom_right, bottom_left))
    
    return quads

if __name__ == "<run_path>":
    
    class curve_section:
        def __init__(self, leftCurve, rightCurve, topCurve, bottomCurve):
            self.leftCurve = leftCurve
            self.rightCurve = rightCurve
            self.topCurve = topCurve
            self.bottomCurve = bottomCurve

    curve_sections = [
        # # ## FRONT
        # curve_section(leftCurve = get_curve_object("GraphTest.010"), rightCurve = get_curve_object("GraphTest.025"), topCurve = get_curve_object("GraphTest.021"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.025"), rightCurve = get_curve_object("GraphTest.026"), topCurve = get_curve_object("GraphTest.023"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.026"), rightCurve = get_curve_object("GraphTest.008"), topCurve = get_curve_object("GraphTest.024"), bottomCurve = get_curve_object("GraphTest.020")),
        
        # ## LEFT
        # curve_section(leftCurve = get_curve_object("GraphTest.008"), rightCurve = get_curve_object("GraphTest.018"), topCurve = get_curve_object("GraphTest.024"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.018"), rightCurve = get_curve_object("GraphTest.017"), topCurve = get_curve_object("GraphTest.024"), bottomCurve = get_curve_object("GraphTest.020")),
        
        # #TODO might need to split 017-016
        # curve_section(leftCurve = get_curve_object("GraphTest.017"), rightCurve = get_curve_object("GraphTest.016"), topCurve = get_curve_object("GraphTest.024"), bottomCurve = get_curve_object("GraphTest.020")),
        
        # curve_section(leftCurve = get_curve_object("GraphTest.016"), rightCurve = get_curve_object("GraphTest.015"), topCurve = get_curve_object("GraphTest.024"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.015"), rightCurve = get_curve_object("GraphTest.014"), topCurve = get_curve_object("GraphTest.024"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.019"), rightCurve = get_curve_object("GraphTest.014"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.024")),
        # curve_section(leftCurve = get_curve_object("GraphTest.014"), rightCurve = get_curve_object("GraphTest.013"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.020")),
        
        ## BACK
        # curve_section(leftCurve = get_curve_object("GraphTest.013"), rightCurve = get_curve_object("GraphTest.012"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.007")),
        # curve_section(leftCurve = get_curve_object("GraphTest.012"), rightCurve = get_curve_object("GraphTest.001"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.007")),
        curve_section(leftCurve = get_curve_object("GraphTest.001"), rightCurve = get_curve_object("GraphTest.002"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.007")),
        
        # ## RIGHT
        # curve_section(leftCurve = get_curve_object("GraphTest.002"), rightCurve = get_curve_object("GraphTest.003"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.003"), rightCurve = get_curve_object("GraphTest.011"), topCurve = get_curve_object("GraphTest.027"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.003"), rightCurve = get_curve_object("GraphTest.011"), topCurve = get_curve_object("GraphTest.009"), bottomCurve = get_curve_object("GraphTest.027")),
        # curve_section(leftCurve = get_curve_object("GraphTest.003"), rightCurve = get_curve_object("GraphTest.011"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.009")),
        # curve_section(leftCurve = get_curve_object("GraphTest.011"), rightCurve = get_curve_object("GraphTest.005"), topCurve = get_curve_object("GraphTest.027"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.011"), rightCurve = get_curve_object("GraphTest.005"), topCurve = get_curve_object("GraphTest.009"), bottomCurve = get_curve_object("GraphTest.027")),
        # curve_section(leftCurve = get_curve_object("GraphTest.011"), rightCurve = get_curve_object("GraphTest.005"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.009")),
        # curve_section(leftCurve = get_curve_object("GraphTest.005"), rightCurve = get_curve_object("GraphTest.022"), topCurve = get_curve_object("GraphTest.004"), bottomCurve = get_curve_object("GraphTest.021")),
        # curve_section(leftCurve = get_curve_object("GraphTest.005"), rightCurve = get_curve_object("GraphTest.006"), topCurve = get_curve_object("GraphTest.021"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.006"), rightCurve = get_curve_object("GraphTest.028"), topCurve = get_curve_object("GraphTest.021"), bottomCurve = get_curve_object("GraphTest.020")),
        # curve_section(leftCurve = get_curve_object("GraphTest.028"), rightCurve = get_curve_object("GraphTest.010"), topCurve = get_curve_object("GraphTest.021"), bottomCurve = get_curve_object("GraphTest.020")),
    ]

    blargPoints = []
    blargFaces = []
    for section in curve_sections:
        blargPoints.extend(get_curve_section_points(section.leftCurve, section.rightCurve, section.topCurve, section.bottomCurve))
        blargFaces.extend(get_15x15_faces(blargPoints))

    print(len(blargPoints))

    create_visualization(blargPoints, [], blargFaces)






            