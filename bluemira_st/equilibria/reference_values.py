"""
Reference scaling values for isoflux, PF and CS coils.
based on openSTEP data from EB-CC/_src/equilibrium.mat.
"""

# Shafranov shift
# scaled to minor radius (a)
REF_SHAF_SHIFT = 0.39238

# PF coil positions
# Diff in x coords for P1 and null, scaled by minor radius
#     dx(P1 - R_x) / a**2
REF_X_P1 = -0.10750
#     dz(P1 - Z_x) / Z_x (plasma height, Z_x)
REF_Z_P1 = 0.38889  # scaled
REF_Z_P1_RAW = 2.380  # not scaled, [m]

# Diff in z coords for P2 and P1, scaled by plasma height (Z_x)
#     dz(P2-P1) / Z_x
REF_Z_P2 = 0.16340
# scaled by heights of P1 and P2 coils
#     dz(P2-P1)/ (P1_h + P2_h)*Z_x
REF_Z_P2_heights = 0.14409
# Diff in x coords for P2 and P1, scaled by minor radius (a)
#      dx(P2-P1) / a
REF_X_P2 = 0.55

# Diff in x coords for P3 and P2, scaled by minor radius (a)
#     dx(P3 - P2) / a
REF_X_P3 = 1.8
REF_X_P3_RAW = 3.6  # [m]

# PF coil sizes
# Aspect ratio of PF coil height to width
REF_ASPECTRATIO_PF1 = 2.49813
REF_ASPECTRATIO_PF2 = 1.27248
REF_ASPECTRATIO_PF3 = 1.54496
REF_ASPECTRATIO_PF4 = 2.68539
REF_ASPECTRATIO_PF5 = 1.81744
# Height scaled to plasma current
REF_HEIGHT_PF1 = 2.9305799648506222e-08
REF_HEIGHT_PF2 = 2.051845342706497e-08
REF_HEIGHT_PF3 = 2.4912126537785598e-08
REF_HEIGHT_PF4 = 3.1502636203866455e-08
REF_HEIGHT_PF5 = 2.9305799648506143e-08

# CS coils
# Full height of CS coils, scaled to plasma height (Z_x)
REF_HEIGHT_CS = 0.14167
REF_HEIGHT_CS_SQ = 0.02315  # divided by Z_x**2
REF_HEIGHT_CS_QU = 0.00062  # by Z**4
# CS coil height / width
REF_ASPECTRATIO_CS = 27.09375
# X coord ref for CS coils nearest the null points, prop. to minor radius (a)
# X_CS_NULL / a
REF_X_CS_NULL = 0.47675
# X_CS_NULL / R_0
REF_X_CS_NULL_R0 = 0.26486

# Z coord ref for CS coil above null, prop. to plasma height (Z_x)
# dz(Z_CS1 - Z_x) / Z_x
REF_Z_CSU = 0.04902
REF_Z_CSU_RAW = 0.3
# Z coord ref for CS coil below null, prop. to plasma height (Z_x)
# dz(Z_CS2 - Z_x) / Z_x
REF_Z_CSL = -0.11765
REF_Z_CSL_RAW = -0.72
# z coord reference for the different between
#     the upper and lower CS coil
REF_CS_SEP = 1.17647
