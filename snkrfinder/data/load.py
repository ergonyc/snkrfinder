# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01b_data.load.ipynb (unless otherwise specified).

__all__ = ['add_subdir', 'creat_full_local_categorydirs', 'create_test_train_directories']

# Cell
from ..imports import *
from ..core import *
from .munge import *

import scipy.io as sio
from sklearn.model_selection import train_test_split
### might be fastai wrappers to do this elegantly... (untar_data?)
import os
import shutil


# Cell

def add_subdir(root,dname):
    l_path = os.path.join(root,dname)
    if not os.path.exists(l_path):
        os.makedirs(l_path)
    return l_path

def creat_full_local_categorydirs(df,lpath,dpath=None):
    # create full set
    print('_'*30)
    print('Creating full local category set....')
    print('_'*30)
    ldata_path = add_subdir(lpath,'raw')
    data_path = dpath if dpath is not None else D_ROOT/DBS['zappos']

    train_path = add_subdir(lpath,'train')
    val_path = add_subdir(lpath,'validate')
    test_path = add_subdir(lpath,'test')

    n_copied = 0
    train_moved = 0
    val_moved = 0
    test_moved = 0
    for idx in df.index:
        save_path = add_subdir(ldata_path,df.loc[idx,'Category'])
        img =  os.path.join(data_path,df.loc[idx,'path'])
        shutil.copy2(img,save_path)
        n_copied += 1

        save_path = add_subdir(ldata_path,df.loc[idx,'Category'])
        img =  os.path.join(data_path,df.loc[idx,'path'])
        shutil.copy2(img,save_path)
        train_moved += 1
    return n_moved



# Cell

def create_test_train_directories(df,lpath,dpath=None):
    "copy the database and split images into test/train sub-directories"
    def _sort_ttv(img,ldata_path,ttv,nttv):
        if ttv=='train':
            nttv['train'] += 1
            save_path = add_subdir(os.path.join(lpath,'train'),df.loc[idx,'Category'])
            shutil.copy2(img,save_path)
        elif ttv=='test':
            nttv['test'] += 1
            save_path = add_subdir(os.path.join(lpath,'test'),df.loc[idx,'Category'])
            shutil.copy2(img,save_path)
        elif ttv=='valid':
            nttv['valid'] += 1
            save_path = add_subdir(os.path.join(lpath,'validate'),df.loc[idx,'Category'])
            shutil.copy2(img,save_path)
        else:
            print(f"error:{img} not t t v")  #TODO: make this propagate an error instead of

    data_path = dpath if dpath is not None else D_ROOT/DBS['zappos']

    ldata_path = add_subdir(lpath,'raw')

    train_path = add_subdir(lpath,'train')
    val_path = add_subdir(lpath,'valid')
    test_path = add_subdir(lpath,'test')

    nttv = {'train':0,'test':0,'valid':0}
    # create test set (copies everything...)
    print('_'*30)
    print('Creating full train/test/validate set (+raw copy)....')
    print('_'*30)

    n_moved = 0
    for idx in df.index:
        save_path = add_subdir(ldata_path,df.loc[idx,'Category'])
        img =  os.path.join(data_path,df.loc[idx,'path'])
        shutil.copy2(img,save_path)
        n_moved += 1

        ttv = df.loc[idx,'t_t_v']
        # now copy it to the destination
        _sort_ttv(img,ldata_path,ttv,nttv)

        #     n_train = nttv['train']
        #     n_valid = nttv['validate']
        #     n_test = nttv['test']

    return n_moved, nttv['train'], nttv['valid'], nttv['test']
