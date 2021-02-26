# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_data.core.ipynb (unless otherwise specified).

__all__ = ['get_zappos_db', 'read_zappos_meta', 'simplify_zappos_db', 'skl_tt_split', 'add_subdir',
           'creat_full_local_categorydirs', 'create_test_train_directories', 'extract_cat', 'extract_brand_goat',
           'extract_brand_sns', 'extract_db_nm', 'get_scraped_db', 'merge_dbs', 'extract_zap_sneakers']

# Cell
from ..imports import *
from ..core import *

import scipy.io as sio
from sklearn.model_selection import train_test_split
### might be fastai wrappers to do this elegantly... (untar_data?)
import os
import shutil


# Cell
def get_zappos_db():
    "import the UT zappos 50k database from vision.cs.utexas.edu"
    # the images are wider than tall with the product already taking up aproximately the whole vertical dimension
    url_images = "http://vision.cs.utexas.edu/projects/finegrained/utzap50k/ut-zap50k-images.zip"
    url_meta = "http://vision.cs.utexas.edu/projects/finegrained/utzap50k/ut-zap50k-data.zip"

    DATA_path = D_ROOT
    meta_path = untar_data(url_meta, dest=DATA_path)
    im_path = untar_data(url_images,dest=DATA_path)

    return meta_path, im_path

# Cell

def read_zappos_meta(path_meta):
    "read the metadat from UT zappos 50k db"

    def _path_from_mat(fname):
        """ reads zappos imagepath from matlab file"""
        data = sio.loadmat(fname)['imagepath']
        return [i[0][0] for i in data]

    image_path = _path_from_mat(path_meta/'image-path.mat')
    df = pd.read_csv(path_meta/'meta-data.csv')

    df["path"]=image_path

    # ad sub-categories (one-hot)
    categories=pd.read_csv(path_meta/'meta-data-bin.csv')
    df = pd.merge(df, categories,  how='left', on='CID')# left_on=['CID'], right_on = ['CID'])


    # fix the path by remove trailing periods in folder names
    df.loc[df.path.str.contains("./",regex=False),"path"] = [i.replace("./","/") for i in df.loc[df.path.str.contains("./",regex=False),"path"]]
    df.loc[df.path.str.contains("Levi\'s ",regex=False),"path"] = [i.replace("Levi\'s ","Levis ") for i in df.loc[df.path.str.contains("Levi\'s ",regex=False),"path"]]
    # create brands and category stubs...
    df['path_and_file'] = df.path.apply(lambda path: (os.path.normpath(path)).split(os.sep) )
    df_to_add = pd.DataFrame(df['path_and_file'].tolist(), columns=['Category1','Category2','Brand','Filename'])

    df = df.merge(df_to_add, left_index=True, right_index=True)
    #df = pd.merge(df, df_to_add, left_index=True, right_index=True)
    return df


# Cell

def simplify_zappos_db(df):
    " simplifies the db (df)"
    # add our "sneaker category"
    df.loc[:,'Sneakers'] = (df['Category2'] == 'Sneakers and Athletic Shoes')

    # refine boot
    df.loc[:,'Boots'] = (  (df.Category1 == 'Boots')
                         & (df.Category2 != 'Knee High')
                         & (df.Category2 != 'Over the Knee')
                         & (df.Category2 != 'Prewalker Boots') )

    # refine shoes
    df.loc[:,'Shoes'] = (  (df.Category1 == 'Shoes')
                         & (df.Category2 != 'Sneakers and Athletic Shoes')
                         & (df.Category2 != 'Heels')
                         & (df.Category2 != 'Crib Shoes')
                         & (df.Category2 != 'Firstwalker')
                         & (df.Category2 != 'Prewalker') )

    # refine shoes
    df.loc[:,'Slippers'] = (  (df.Category1 == 'Slippers')
                         & (df.Category2 != 'Boot') )


    ############
    #remove ([ 'Boys',  'Boys;Girls', 'Girls','Women;Girls', nan

    mens =  df['Gender'] == 'Men'
    womens =  df['Gender'] == 'Women'
    etc =  df['Gender'].str.contains('Men;', na=False)

    df.loc[:,'Adult'] = mens | womens | etc

    df.loc[:,'Mens'] = mens
    df.loc[:,'Womens'] = womens

    df.loc[:,'OGcategory'] = df.Category
    df.loc[:,'Category'] = pd.NA

    df.loc[(df.Shoes==1),'Category'] = 'Shoes'
    df.loc[(df.Boots==1),'Category'] = 'Boots'
    df.loc[(df.Sneakers==1),'Category'] = 'Sneakers'
    df.loc[(df.Slippers==1),'Category'] = 'Slippers'


    # make some expository columns
    keep_columns = ['CID','Category',
                     'path','path_and_file',
                     'Category1', 'Category2','OGcategory'
                     'Brand','Filename',
                     'Sneakers','Boots',
                     'Shoes', 'Slippers','Adult',
                     'Gender']

    df = df.filter(items=keep_columns)
    #keep Adult, Sneakers, Boots, Shoes, Slippers
    keep_rows = (df.Sneakers | df.Boots | df.Shoes| df.Slippers) & (df.Adult)
    #Only keep Adult (men+women) and Sneakers, Boots, Shoes
    df = df[keep_rows.values]
    return df

# Cell

def skl_tt_split(df,strat_cat):
    "adds stratified train-validate-test via sklearn"


    X = df.index
    y = strat_cat

    train_ratio = 0.70
    validation_ratio = 0.15

    # keep
    test_ratio = 0.15

    # train is now 75% of the entire data set
    # the _junk suffix means that we drop that variable completely
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=1 - train_ratio,stratify=y, random_state=666)

    # test is now 10% of the initial data set
    # validation is now 15% of the initial data set
    x_val, x_test, y_val, y_test = train_test_split(x_test, y_test, test_size=test_ratio/(test_ratio + validation_ratio),stratify=y_test, random_state=666)
    # pack into the dataframe
    df.loc[:,'train'] = False
    df.loc[:,'test'] = False
    df.loc[:,'validate'] = False
    df.loc[:,'t_t_v'] = 'train'
    df.loc[x_train,'train'] = True
    df.loc[x_test,'test'] = True
    df.loc[x_val,'validate'] = True
    df.loc[x_test,'t_t_v'] = 'test'
    df.loc[x_val,'t_t_v'] = 'valid'
    return df



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


# Cell
def extract_cat(lst):
    for l in lst:
        if l.startswith("CATEGORY"):
            return l.split("\n")[-1]
    return "na" #np.nan

def extract_brand_goat(lst):
    for l in lst:
        if l.startswith("BRAND"):
            return l.split("\n")[-1]
    return "na"

def extract_brand_sns(lst):
    return lst[1]

def extract_db_nm(pathn):
    return pathn.split('/')[0]


# Cell
def get_scraped_db():
    "collect meta data fromscraped databases"

    def _extract_cat(lst):
        for l in lst:
            if l.startswith("CATEGORY"):
                return l.split("\n")[-1]
        return "na" #np.nan

    def _extract_brand_goat(lst):
        for l in lst:
            if l.startswith("BRAND"):
                return l.split("\n")[-1]
        return "na"

    def _extract_brand_sns(lst):
        return lst[1]

    def _extract_db_nm(pathn):
        return pathn.split('/')[0]

    df_scraped = pd.read_pickle(f"{SCRAPED_META_DIR/SCRAPED_DF}.pkl")
    df_scraped.loc[:,"path"]=df_scraped.hero_fullpath.str.split('/').apply(lambda x: 'scraped/'+x[-3]+'/'+x[-1])
    df_scraped.loc[:,"brand"]=df_scraped.attributes.apply(_extract_brand_sns)
    df_scraped.loc[:,"cat"]=df_scraped.attributes.apply(_extract_cat)
    df_scraped.loc[:,"db_name"]=df_scraped["path"].apply(_extract_db_nm)
    df_scraped.loc[df_scraped['db_name']=='goat',"brand"]=df_scraped.loc[df_scraped['db_name']=='goat',"attributes"].apply(_extract_brand_goat)
    return df_scraped


# Cell
def merge_dbs(df_zappos,df_scraped):
    "could be any dfs with 'path','train','test','validate','t_t_v'"
    # TODO:  add "is_valid" wiich is test and (so validate are part of test)?)
    return pd.merge(df_zappos,df_scraped,how='outer',on=['path','train','test','validate','t_t_v'])

# Cell

def extract_zap_sneakers(df_zappos):
    return df_zappos[df_zappos['Sneakers']]