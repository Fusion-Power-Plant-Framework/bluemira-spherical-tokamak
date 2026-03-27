from pathlib import Path

from bluemira.base.reactor_config import ReactorConfig

from bluemira_st.build_routines import build_reference_equilibrium
from bluemira_st.params import BluemiraSTParams

build_config_path = Path(Path(__file__).parent, "config/config.json").resolve()
reactor_config = ReactorConfig(build_config_path, BluemiraSTParams)

test_fbe = build_reference_equilibrium(
    reactor_config.params_for("reference_fbe").global_params,
    reactor_config.config_for("reference_fbe"),
)


# x_c = [2.15, 3.25, 6.85, 6.85, 8.3]
# z_c = [8.5, 9.5, 9.6, 6.35, 2.1]


# x_cs = [0.9535, 0.9535]
# z_cs = [6.42, 5.4]
