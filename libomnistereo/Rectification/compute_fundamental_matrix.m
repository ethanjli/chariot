function F = compute_fundamental_matrix ( T, om)

F = [ 0, -T(3), T(2); T(3), 0, -T(1); -T(2), T(1),0] * rodrigues(om);