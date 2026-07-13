from bluemira.equilibria.equilibrium import Equilibrium
from bluemira.geometry.coordinates import Coordinates
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from bluemira.geometry.face import BluemiraFace
from matplotlib.path import Path
import numpy as np

def extract_field_map(eq, tf_coil, stride=1):
    """
    Extract magnetic field grid, downsample if required, and flatten.

    Returns
    -------
    points : (N, 2)
        (R, Z) coordinates
    fields : dict
        Flattened field components
    """
    # plasma equilibrium grid
    grid = eq.grid

    # Downsample
    R = grid.x[::stride, ::stride]
    Z = grid.z[::stride, ::stride]
    zeros = np.zeros_like(R)
    Br = eq.Bx()[::stride, ::stride]
    Bz = eq.Bz()[::stride, ::stride]
    Bp = eq.Bp()[::stride, ::stride]
    # vacuum toroidal field from TF coils
    Bt = eq.Bt(x=R)

    helmholtz_field = tf_coil.field(R,zeros,Z)
    Bt_helmholtz = helmholtz_field[1]
    print(np.shape(Bt))
    print(np.shape(Bt_helmholtz))

    # Flatten
    points = np.column_stack([R.ravel(), Z.ravel()])

    fields = {
        "Br": Br.ravel(),
        "Bz": Bz.ravel(),
        "Bp": Bp.ravel(),
        "Bt": Bt.ravel(),
        "Bt_helmholtz": Bt_helmholtz.ravel()
    }

    return points, fields


def blanket_polygon(face, resolution=400):

    boundary = face.discretise(resolution)
    print(np.shape(boundary[0]))
    x_b = boundary[0][:, 0]
    z_b = boundary[0][:, 2]

    polygon = Path(
        np.column_stack([x_b, z_b])
    )

    return polygon

def mask_and_export(points, fields, polygon, filename=None):
    """
    Filter field data inside polygon and compute |B|.
    Parameters
    ----------
    points : (N, 2)
    fields : dict of arrays
    polygon : Path
    filename : str or None

    Returns
    -------
    data : dict
    """

    mask = polygon.contains_points(points)

    # Base data
    data = {
        "R": points[:, 0][mask],
        "Z": points[:, 1][mask],
        "Br": fields["Br"][mask],
        "Bz": fields["Bz"][mask],
        "Bp": fields["Bp"][mask],
        "Bt": fields["Bt"][mask],
        "Bt_helmholtz": fields["Bt_helmholtz"][mask]
    }

    # Magnetic field magnitude
    data["Bmag"] = np.sqrt(
        data["Br"]**2 +
        data["Bz"]**2 +
        data["Bt_helmholtz"]**2
    )

    # Export
    if filename is not None:
        out = np.column_stack([
            data["R"],
            data["Z"],
            data["Br"],
            data["Bz"],
            data["Bp"],
            data["Bt"],
            data["Bt_helmholtz"],
            data["Bmag"],
        ])

        header = "R Z Br Bz Bp Bt Bt_helmholtz Bmag"
        np.savetxt(filename, out, header=header)

    return data


def plot_Bmap(data, data_field="Bmag"):
    "plot magnetic field map in blanket region"
    plt.figure(figsize=(6, 6))
    sc = plt.scatter(
        data["R"],
        data["Z"],
        c=abs(data[str(data_field)]),
        s=7,              # marker size
        cmap="viridis"
    )

    plt.colorbar(sc, label="|B| [T]")
    plt.xlabel("R [m]")
    plt.ylabel("Z [m]")
    plt.title("Magnetic Field Magnitude in Blanket Region: "+str(data_field))
    plt.axis("equal")

    plt.show()
