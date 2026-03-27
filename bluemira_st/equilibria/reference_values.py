"""
Reference scaling values for isoflux, PF and CS coils.
Based on openSTEP data from EB-CC/_src/coilset.mat and equilibrium.mat.
"""

# Shafranov shift
# scaled to minor radius (a)
SHAF_SHIFT = 0.39238

# -----
# PF coil positions
# -----
# Diff in x coords for P1 and null, scaled by minor radius squared
# dx(P1 - R_x) / a**2
X_P1 = -0.10750

# dz(P1 - Z_x) / Z_x (plasma height, Z_x)
Z_P1 = 0.38889
Z_P1_RAW = 2.380  # not scaled, [m]

# Diff in x coords for P2 and P1, scaled by minor radius (a)
# dx(P2-P1) / a
X_P2 = 0.55

# Diff in z coords for P2 and P1, scaled by plasma height (Z_x)
# dz(P2-P1) / Z_x
Z_P2 = 0.16340

# -----
# PF coil sizes
# -----
# Aspect ratio of PF coil height to width
ASPECTRATIO_PF1 = 2.49813
ASPECTRATIO_PF2 = 1.27248
ASPECTRATIO_PF3 = 1.54496
ASPECTRATIO_PF4 = 2.68539
ASPECTRATIO_PF5 = 1.81744
# Height scaled to plasma current
HEIGHT_PF1 = 2.9305799648506222e-08
HEIGHT_PF2 = 2.051845342706497e-08
HEIGHT_PF3 = 2.4912126537785598e-08
HEIGHT_PF4 = 3.1502636203866455e-08
HEIGHT_PF5 = 2.9305799648506143e-08

# -----
# CS coils
# -----
# Full height of CS coils, scaled to plasma height (Z_x)
HEIGHT_CS = 0.14167

# CS coil height / width
ASPECTRATIO_CS = 27.09375

# X coord ref for CS coils nearest the null points
# X_CS_NULL / R_0
X_CS_NULL_R0 = 0.26486

# Z coord reference for the separation in z between
# the CS coils either side of the null
CS_SEP = 1.17647
