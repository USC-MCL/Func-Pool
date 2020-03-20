# v2020.02.05
# PixelHop
#
# PixelHop_Unit: single layer 
##   X: <4-D array>, (N, H, W, D)
##   train: <bool> False: using saab to get weight; True: loaded pre-achieved parameter from par
##   par: parameters needed for testing stage
## do not need following when "train=False":
##   dilate: <list/np.array> dilate for pixelhop (default: 1)
##   pad: <'reflect'/'none'/'zeros'> padding method (default: 'reflect)
##   SaabArg <dict> arguments passed to Saab, ex {'num_AC_kernels':-1, 'needBias':False, 'useDC':True, 'batch':None}
## optional:
##   batch: <int/None> minbatch for saving memory 
#
# Pixelhop: multi layer Pixelhop_Unit no padding involved
##   X: same above
##   train: same above
##   pars: <dict> save par from each PixelHop_Unit, ex {'Layer0':par above}
## do not need following when "train=False":
##   depth: <int> number of PixelHop_Unit
##   dilates: <list/np.array> dilates at each PixelHop_Unit
##   pads: <list> pad method at each layer
##   SaabArgs: <list> of SaabArg
## optional:
##   batch: same above

# both return <4-D array, shape (N, H_new, W_new, D_new)>, <dict> parameter

import numpy as np 
import pickle

from saab import Saab

def PixelHop_Neighbour(feature, dilate, pad):
    dilate = np.array(dilate)
    idx = [1, 0, -1]
    H, W = feature.shape[1], feature.shape[2]
    res = feature.copy()
    if pad == 'reflect':
        feature = np.pad(feature, ((0,0),(dilate[-1], dilate[-1]),(dilate[-1], dilate[-1]),(0,0)), 'reflect')
    elif pad == 'zeros':
        feature = np.pad(feature, ((0,0),(dilate[-1], dilate[-1]),(dilate[-1], dilate[-1]),(0,0)), 'constant', constant_values=0)
    elif pad == 'none':
        H, W = H - 2*dilate[-1], W - 2*dilate[-1]
        res = feature[:, dilate[-1]:dilate[-1]+H, dilate[-1]:dilate[-1]+W].copy()
    else:
        assert (False), "Error padding method! support 'reflect', 'zeros', 'none'."
    for d in range(dilate.shape[0]):
        for i in idx:
            for j in idx:
                if i == 0 and j == 0:
                    continue
                else:
                    ii, jj = (i+1)*dilate[d], (j+1)*dilate[d]
                    res = np.concatenate((feature[:, ii:ii+H, jj:jj+W], res), axis=3)
    return res 

def Batch_PixelHop_Neighbour(feature, dilate, pad, batch):
    if batch <= feature.shape[0]:
        res = PixelHop_Neighbour(feature[0:batch], dilate, pad)
    else:
        res = PixelHop_Neighbour(feature, dilate, pad)
    for i in range(batch, feature.shape[0], batch):
        if i+batch <= feature.shape[0]:
            res = np.concatenate((res, PixelHop_Neighbour(feature[i:i+batch], dilate, pad)), axis=0)
        else:
            res = np.concatenate((res, PixelHop_Neighbour(feature[i:], dilate, pad)), axis=0)
    return res

def PixelHop_Unit(X, train=True, par=None, dilate=[1], pad='reflect', SaabArg=None, batch=None):
    assert (len(X.shape) == 4), "Input must be a 4D array!"
    if train == True:
        par = {'dilate': dilate, 'pad': pad, 'SaabArg': SaabArg, 'Saab': None}
    else:
        assert (par != None), "Parameter must be passed during testing stage!"
    if batch == None:
        X = PixelHop_Neighbour(X, par['dilate'], par['pad'])
    else:
        X = Batch_PixelHop_Neighbour(X, par['dilate'], par['pad'], batch)
    S = X.shape
    X = X.reshape(-1, X.shape[-1])
    par['Saab'] = Saab(num_kernels=par['SaabArg']['num_AC_kernels'], useDC=par['SaabArg']['useDC'], needBias=par['SaabArg']['needBias'])
    par['Saab'].fit(X)
    X = par['Saab'].transform(X)
    X = X.reshape(S[0], S[1], S[2], -1)
    return X, par

if __name__ == "__main__":
    from sklearn.linear_model import LogisticRegression
    from sklearn import datasets
    
    # read data
    print(" \n> This is a test enample: ")
    digits = datasets.load_digits()
    X = digits.images.reshape((len(digits.images), 8, 8, 1))
    print(" input feature shape: %s"%str(X.shape))
    SaabArg = {'num_AC_kernels':-1, 'needBias':False, 'useDC':True}

    # run
    X1, par = PixelHop_Unit(X, train=True, dilate=[1], pad='reflect', par=None, SaabArg=SaabArg, batch=None)
    print(" --> train feature shape: ", X1.shape)
    X2, par = PixelHop_Unit(X, train=False, par=par, batch=None)
    print(" --> test feature shape: ", X2.shape)
    print("------- DONE -------\n")

