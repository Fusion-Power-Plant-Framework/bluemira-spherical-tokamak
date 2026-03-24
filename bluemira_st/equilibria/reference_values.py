"""
Reference scaling values for isoflux, PF and CS coils.
based on openSTEP data from EB-CC/_src/equilibrium.mat.
"""

# Shafranov shift
# scaled to minor radius (a)
REF_SHAF_SHIFT = 0.39238

# PF coil positions
# Diff in x coords for P1 and null, scaled by minor radius
# dx(P1 - R_x) / a
REF_X_P1 = -0.215
# dz(P1 - Z_x) / Z_x (plasma height, Z_x)
REF_Z_P1 = 0.51886  # scaled
REF_Z_P1_RAW = 2.9  # not scaled, [m]

# Diff in z coords for P2 and P1, scaled by plasma height (Z_x)
# dz(P2-P1) / Z_x
REF_Z_P2 = 0.179

# Diff in x coords for P3 and P2, scaled by minor radius (a)
# dx(P3 - P2) / a
REF_X_P3 = 1.8
REF_X_P3_RAW = 3.6  # [m]

# CS coils
# Full height of CS coils, scaled to plasma height (Z_x)
REF_HEIGHT_CS = 0.15482
# CS coil height / width
REF_ASPECTRATIO_CS = 27.09375
# X coord ref for CS coils nearest the null points, prop. to minor radius (a)
# X_CS_NULL / a
REF_X_CS_NULL = 0.47675
# Z coord ref for CS coil above null, prop. to plasma height (Z_x)
# dz(Z_CS1 - Z_x) / Z_x
REF_Z_CSU = 0.14643
# Z coord ref for CS coil below null, prop. to plasma height (Z_x)
# dz(Z_CS2 - Z_x) / Z_x
REF_Z_CSL = -0.03571
