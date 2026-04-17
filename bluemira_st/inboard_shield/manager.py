from bluemira.base.reactor import ComponentManager
from bluemira.geometry.face import BluemiraFace

from bluemira_st.inboard_shield.builder import ISBuilder


class IS(ComponentManager):
    """Inboard Shield component manager."""

    def xz_face(self) -> BluemiraFace:
        """Get the 2D xz face of the inboard shield."""
        return self.component().get_component("xz").get_component(ISBuilder.IS).shape
