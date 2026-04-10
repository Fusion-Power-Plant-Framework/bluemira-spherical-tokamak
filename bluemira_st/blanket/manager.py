from bluemira.base.reactor import ComponentManager
from bluemira.geometry.face import BluemiraFace

from bluemira_st.blanket.builder import BBBuilder


class BB(ComponentManager):
    """Breeding blanket component manager."""

    def xz_face(self) -> BluemiraFace:
        """Get the 2D xz face of the breeding blanket."""
        return self.component().get_component("xz").get_component(BBBuilder.BB).shape
