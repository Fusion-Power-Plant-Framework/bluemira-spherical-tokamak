import pandas as pd
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
        inboard_wire[0].end_point(),
        blanket_wire[3].start_point(),
    ])
    points2 = Coordinates([
        blanket_wire[3].end_point(),
        inboard_wire[0].start_point(),
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


def charged_particle_calculation(
    eq,
    fw_shape_coords,
    params: dict,
):
    show_plot = False
    solver = ChargedParticleSolver(params, eq, dx_mp=0.001)
    x, z, hf = solver.analyse(first_wall=fw_shape_coords)
    solver.plot(show=show_plot)
    return x, z, hf


def export_charged_particle_to_csv(x, z, cpf, filename="charged_particle_results.csv"):
    data = {
        "x": x,
        "z": z,
        "charged_particle_flux": cpf,
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
