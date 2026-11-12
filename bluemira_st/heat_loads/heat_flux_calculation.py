import matplotlib.pyplot as plt
from bluemira.geometry.coordinates import Coordinates
from bluemira.geometry.tools import make_polygon
from bluemira.geometry.wire import BluemiraWire
from bluemira.radiation_transport.advective_transport import ChargedParticleSolver


def fw_shape(blanket, inboard_shield):

    # import or create first wall shape
    # import fw faces (no real fw defined yet)
    blanket_wire = blanket.xz_face().edges
    inboard_wire = inboard_shield.xz_face().edges

    # FROM INTERACTIVE SESSION
    points1 = Coordinates([
        blanket_wire[0].start_point(),
        inboard_wire[0].start_point(),
    ])
    points2 = Coordinates([
        inboard_wire[0].end_point(),
        blanket_wire[2].start_point(),
    ])
    upper_wire = make_polygon(points1)
    lower_wire = make_polygon(points2)
    fw_wire = BluemiraWire([
        inboard_wire[0],
        lower_wire,
        blanket_wire[3],
        upper_wire,
    ])
    return fw_wire.discretise()


def heat_flux_calculation(fw_shape_coords, eq):
    params = {
        "P_sep_particle": 1.79999999999817703e02,  # PROCESS
        "f_p_sol_near": 0.65,
        "fw_lambda_q_near_omp": 0.003,
        "fw_lambda_q_far_omp": 0.1,
        "fw_lambda_q_near_imp": 0.003,
        "fw_lambda_q_far_imp": 0.1,
        "f_lfs_lower_target": 0.9 * 0.5,
        "f_hfs_lower_target": 0.1 * 0.5,
        "f_lfs_upper_target": 0.9 * 0.5,
        "f_hfs_upper_target": 0.1 * 0.5,
    }
    solver = ChargedParticleSolver(params, eq, dx_mp=0.001)

    x, z, hf = solver.analyse(first_wall=fw_shape_coords)
    solver.plot()
    plt.show()
    return x, z, hf
