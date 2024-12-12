#   File "/home/oliver/development/PROCESS/process/io/in_dat.py", line 895, in get_value
#     return parameter_type(self.name, self.value)
#            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/home/oliver/development/PROCESS/process/io/in_dat.py", line 695, in parameter_type
#     param_type = dicts["DICT_VAR_TYPE"][name]
#                  ~~~~~~~~~~~~~~~~~~~~~~^^^^^^
# KeyError: 'fwcoolant'


from process.io.in_dat import InDat

in_dat = InDat(filename="./st_regression.IN.DAT")
[print(k, v.value if k == "runtitle" else v.get_value) for k, v in in_dat.data.items()]
