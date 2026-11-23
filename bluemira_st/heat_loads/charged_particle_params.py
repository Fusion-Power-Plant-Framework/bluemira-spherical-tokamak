"""Parameters for the Bluemira ST example charged-particle heat-flux calculation."""

CHARGED_PARTICLE_PARAMS = {
    "P_sep_particle": 1.79999999999817703e02,  # MW, from PROCESS
    "f_p_sol_near": 0.65,
    "fw_lambda_q_near_omp": 0.003,  # m
    "fw_lambda_q_far_omp": 0.1,  # m
    "fw_lambda_q_near_imp": 0.003,  # m
    "fw_lambda_q_far_imp": 0.1,  # m
    "f_lfs_lower_target": 0.9 * 0.5,
    "f_hfs_lower_target": 0.1 * 0.5,
    "f_lfs_upper_target": 0.9 * 0.5,
    "f_hfs_upper_target": 0.1 * 0.5,
}
