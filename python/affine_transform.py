import numpy as np
import mathutils
from collections.abc import Awaitable, Callable, Iterable, Iterator, MutableSet, Reversible, Set as AbstractSet, Sized

def transform_points_from_BY_to_AZ(B : np.ndarray, Y : np.ndarray, A : np.ndarray, Z : np.ndarray, points : Iterable[np.ndarray]):

    # # Coordinates of the original segment
    # B = np.array([x_B, y_B, z_B])
    # Y = np.array([x_Y, y_Y, z_Y])

    # # Coordinates of the target segment
    # A = np.array([x_A, y_A, z_A])
    # Z = np.array([x_Z, y_Z, z_Z])


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



if __name__ == "<run_path>":


    B = np.array([0, 0, 0])
    Y = np.array([0, 1, 0])

    A = np.array([0, 0, 0])
    Z = np.array([0, 0, 2])

    points = [ np.array([0, -1, 0]) ]

    t_P = transform_points_from_BY_to_AZ(B, Y, A, Z, points)


    print(f"{t_P}")
    