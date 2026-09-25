import re

from bluemira.base.reactor import ComponentManager
from bluemira.equilibria import Equilibrium
from bluemira.geometry.face import BluemiraFace

from bluemira_st.blanket.builder import BBBuilder
from bluemira_st.magnetostatics.map import (
    extract_field_map,
    face_to_mpl_path,
    mask_and_export,
    plot_Bmap,
)
from bluemira_st.tf_coil.manager import TFCoil


class BreedingBlanket(ComponentManager):
    """Breeding blanket component manager."""

    def xz_face(self) -> BluemiraFace:
        """Get the 2D xz face of the breeding blanket."""
        return self.component().get_component("xz").get_component(BBBuilder.BB).shape

    def create_field_map(self, eq: Equilibrium, tf: TFCoil, filename: str | None = None):
        """Create field map of component."""
        points, fields = extract_field_map(eq, tf)
        polygon = face_to_mpl_path(self.xz_face())
        data = mask_and_export(points, fields, polygon, filename)
        plot_Bmap(data, "Bmag", re.sub(r"(\w)([A-Z])", r"\1 \2", type(self).__name__))
