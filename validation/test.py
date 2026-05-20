import numpy as np


arr1 = np.asarray([[1,2], [3,4]])
mask = np.where(arr1 < 3)
print(mask)