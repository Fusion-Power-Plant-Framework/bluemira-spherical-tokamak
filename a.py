from bluemira.geometry.parameterisations import TripleArc
from matplotlib import pyplot as plt

TripleArc({
    "x1": {"value": 10, "fixed": True},
    "f1": {
        "value": 1,
    },
}).plot(labels=True)
TripleArc({
    "x1": {"value": 10, "fixed": True},
    "f1": {
        "value": 10,
    },
}).plot(labels=True)
plt.show()
