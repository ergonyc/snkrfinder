# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02a_model.core.ipynb (unless otherwise specified).

__all__ = ['get_cuda', 'get_cpu', 'AdaptiveConcatPoolFlat', 'get_mnetV2_feature_net', 'get_rnet_feature_net',
           'create_cnn_featurenet', 'FeatsResize', 'zap_get_x', 'zap_get_y', 'zap_get_fname',
           'get_zap_feats_dataloaders', 'get_all_feats', 'get_feats_df', 'save_feats', 'save_featsXsize',
           'collate_featsXsize', 'get_convnet_feature', 'load_and_prep_sneaker', 'load_and_prep_tf_pipe',
           'get_umap_reducer', 'get_neighs_and_reducers', 'query_neighs', 'get_similar_images', 'plot_sneak_neighs',
           'get_umap_embedding']

# Cell
from ..imports import *
from ..core import *
from ..data import *

from sklearn.neighbors import NearestNeighbors

import umap #!conda install -c conda-forge umap-learn
import seaborn as sns

from sklearn.decomposition import PCA
from sklearn.metrics import confusion_matrix, plot_confusion_matrix
from seaborn import heatmap
from sklearn.linear_model import LogisticRegression




# Cell

# these are pure torch wrappers... should replace with fastai calls.
def get_cuda():
    """ try to load onto GPU"""
    return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def get_cpu():
    """
    set device to cpu.
    """
    return torch.device("cpu")

# Cell
class AdaptiveConcatPoolFlat(nn.Module):
    """
    torch implimentation of fastai's ConcatPool with a flattend output
    """
    def __init__(self):
        super().__init__()
        self.ap = nn.AdaptiveAvgPool2d((1,1))
        self.mp = nn.AdaptiveMaxPool2d((1,1))

    def forward(self, x):
        return torch.cat([self.mp(x), self.ap(x)], 1).view(x.shape[0],-1)

def get_mnetV2_feature_net(to_cuda=False):
    # we want to collapse the features across spatial dimension

    device = get_cuda() if to_cuda else get_cpu()

    arch  = torchvision.models.mobilenet_v2(pretrained=True)
    #     # simply grafting into the "classifier" doesn't play nice with the torchvision
    #     mnetv2.classifier = MyAdaptiveConcatPoolFlat()

    #so we need to recast it:
    features = nn.Sequential(*list(arch.children())[0])
    mnet = nn.Sequential(features, AdaptiveConcatPoolFlat()).to(device)

    mnet.eval()  # force it to eval mode to turn off batchnorm/dropout

    # just incase we forget the no_grad()
    for param in mnet.parameters():
        param.requires_grad = False

    mnet.name = arch.__class__.__name__
    return mnet

# Cell

def get_rnet_feature_net(to_cuda=False):
    # there's also a create_body create_head fastai builtin helper
    arch,cut = xresnet18(pretrained=True),-4
    model = nn.Sequential(*list(arch.children())[:cut],
                               AdaptiveConcatPool2d(),
                               Flatten())

    device = get_cuda() if to_cuda else get_cpu()

    model = model.to(device)
    model.eval()  # force it to eval mode to turn off batchnorm/dropout

    # just incase we forget the no_grad()
    for param in model.parameters():
        param.requires_grad = False

    model.name = 'resnet18'
    return model




# Cell
# # copied the split and cut from denseness ... need to check if the splits and cut make sense
# def _mobilenet_v2_split(m:torch.nn.Module):
#     return L(m[0][0][:7],m[0][0][7:], m[1:]).map(params)
# # avoid underscore mobilenet_v2_meta to make sure it imports correctly
# mobilenet_v2_meta   = {'cut':-1, 'split':_mobilenet_v2_split, 'stats':imagenet_stats}

# model_meta[torchvision.models.mobilenet_v2] = {**mobilenet_v2_meta}

# export
def create_cnn_featurenet(archname,cut=None, to_cuda=False):
    "archname as string,e.g. mobilenet_v2, resnet, xresnet, etc"
    # one line to make the model

    arch = torchvision.models.mobilenet_v2 if archname.startswith('mobilenet') else eval(archname)

    model = create_cnn_model(arch,cut,custom_head=nn.Sequential(AdaptiveConcatPool2d(),Flatten()) )

    device = get_cuda() if to_cuda else get_cpu()
    model = model.to(device)
    model.eval()  # force it to eval mode to turn off batchnorm/dropout

    # just incase we forget the no_grad()
    for param in model.parameters():
        param.requires_grad = False

    model.name = archname
    return model

# Cell

class FeatsResize(Resize):
    "Simple Resize with the split_idx hacked to always be in `valid` mode"
    def before_call(self, b, split_idx):
        if self.method==ResizeMethod.Squish: return
        self.pcts = (0.5,0.5)



def zap_get_x(r): return D_ROOT/DBS['zappos']/r['path']
def zap_get_y(r): return r['Category']  # we aren't actually using the category here (see transfer learning)
def zap_get_fname(r): return r['path']

def get_zap_feats_dataloaders(data,batch_size, size, device):
    "get the zappos data ready for feature extraction"
    dblock = DataBlock(blocks=(ImageBlock, CategoryBlock),
                   splitter=IndexSplitter([]),
                   get_x=zap_get_x,
                   get_y=zap_get_fname,
                   item_tfms=FeatsResize(size, method='pad', pad_mode='border'),
                   batch_tfms=Normalize.from_stats(*imagenet_stats))  # border pads white...
    dls = dblock.dataloaders(data,bs=batch_size,drop_last=False,device=device)
    #since we are just calculating the features for all the data turn off shuffling
    dls.train.shuffle=False
    return dls

# Cell

def get_all_feats(dls,model,to_df=False):
    " expect dls to give us sorted (alphabetical)"
    outs = []
    clss = []
    paths = []
    batchn = 0

    with torch.no_grad():
        for imgs,classes in dls.train:
            outs.extend(to_detach(conv_net(imgs)))
            clss.extend(to_detach(classes))
            paths.extend( [to_detach(dls[0].vocab[c]) for c in classes])
            batchn += 1


    feats = np.stack(outs)
    cs = np.stack(clss)
    fns = np.stack(paths)
    print(f"processed {batchn} batches")
    return feats,cs,fns

# Cell
def get_feats_df(dls,conv_net):
    outs = []
    clss = []
    paths = []
    batchn = 0

    with torch.no_grad():
        for imgs,classes in dls.train:
            outs.extend(to_detach(conv_net(imgs)))
            clss.extend(to_detach(classes))
            paths.extend( [to_detach(dls[0].vocab[c]) for c in classes])
            batchn += 1
    # not sure why i did this... stack should work.
    out = [np.array(o) for o in outs] #np.stack(to_detach(outs))
    cs = np.stack(clss)
    fn = np.stack(paths)

    print(f"packing {batchn} batches into dataframe")

    #store all relevant info in a pandas datafram
    df_feats = pd.DataFrame({"path": fn, "classes":cs, "features":out})
    return df_feats

# Cell
def save_feats(df,model,im_size,batch_size=64,f_sfx=''):
    device = get_cuda()
#     # might not need to reduce batch_size if my GPU is _clean_
#     bs = batch_size if im_size<=192 else batch_size//2
    dls = get_zap_feats_dataloaders(df,batch_size,im_size,device)
    df_f = get_feats_df(dls,model)
    # save it
    filename = f"{model.name}-features_{f_sfx}" #filename = f"mobilenetv2-features_{sz}"
    df_f.to_pickle(f"data/{filename}.pkl")
    del dls


def save_featsXsize(df,model,im_sizes = IMG_SIZES,batch_size=64):
    for i,sz in enumerate(im_sizes):
        im_size = im_sizes[sz]
        print(im_size)
        save_feats(df,model,im_size,batch_size,sz)




# Cell
def collate_featsXsize(df,mname,im_sizes=IMG_SIZES,dump=True):
    """
    merge the features from small/med/large\
    im_sizes must be adictionary with a str key and int size
    """
    dfs=[]
    for i,sz in enumerate(im_sizes):
        print(im_sizes[sz])
        filename = f"{mname}-features_{sz}"
        dfs.append(pd.read_pickle(f"data/{filename}.pkl"))

    # this is hard coded for now...with sm,md,lg...
    df_test = pd.merge(dfs[0],dfs[1],how='left',on='path',suffixes=('_sm','_md'))
    df_test = pd.merge(df_test,dfs[2],how='left',on='path')
    df_test = df_test.rename(columns={"classes": "classes_lg", "features": "features_lg"})


    #df2 = df.merge(df_feat)
    # explicitly:
    df2 = pd.merge(df, df_test,  how='left', on='path')

    # save it
    if dump:
        filename = f"zappos-50k-{mname}-features_"
        df2.to_pickle(f"data/{filename}.pkl")

    df2 = df2.sort_values('path', ascending=True)
    df2 = df2.reset_index(drop=True)
    if dump:
        filename = f"zappos-50k-{mname}-features_sort_3"
        df2.to_pickle(f"data/{filename}.pkl")

    return df2

# Cell
def get_convnet_feature(cnet,t_image,to_cuda=False):
    """
    input:
        convnet - our neutered & prepped Convolutional Net e.g. MobileNet_v2
        t_image - ImageTensor. probaby 3x224x224... but could be a batch
        to_cuda - send to GPU?  default is CPU (to_cuda=False)
    output:
        features - output of convnet. e.g. mnetv2 -> 2*1280
    """

    # this is redundant b ut safe
    device = get_cuda() if to_cuda else get_cpu()

    cnet = cnet.to(device)
    t_image = t_image.to(device)

    if len(t_image.shape)<4:
        t_image = t_image.unsqueeze(0)

    with torch.no_grad():
        features = cnet(t_image)

    return features


# Cell
def load_and_prep_sneaker(image_path,size=IMG_SIZE,to_cuda=False):
    """ a function to _pipeline_ our images into tensors """

    base_im = PILImage.create(image_path)
    #BUG: pass split_idx=1 to avoid funny business
    img = FeatsResize(size, method='pad', pad_mode='border')(base_im)
    t2 = ToTensor()(img)
    t2 = IntToFloatTensor()(t2)
    t2 = torchvision.transforms.Normalize(*imagenet_stats)(t2)

    device = get_cuda() if to_cuda else get_cpu()

    return t2.to(device)

# Cell


load_and_prep_tf_pipe = Pipeline([PILImage.create,
                 #BUG: pass split_idx=1 to avoid funny business
                 FeatsResize(size=IMG_SIZE, method='pad', pad_mode='border'),
                 ToTensor(),
                 IntToFloatTensor(),
                 Normalize.from_stats(*imagenet_stats,cuda=False)]
               )

    #BUG: pass split_idx=1 to avoid funny business


# Cell
def get_umap_reducer(latents):
    reducer = umap.UMAP(random_state=666)
    reducer.fit(latents)

    return reducer

# Cell

def get_neighs_and_reducers(df,num_neighs=5):
    # pack a dictionary of knns and reducers

    knns = {}
    reducers = {}
    for sz in IMG_SIZES:
        print(f"{sz} {SIZE_ABBR[sz]} {IMG_SIZES[sz]}")

        features = f"features_{SIZE_ABBR[sz]}"
        print(features)

        db_feats = np.vstack(df[features].values)

        neighs = NearestNeighbors(n_neighbors=num_neighs) #add plus one in case image exists in database
        neighs.fit(db_feats)
        knns[sz] = neighs

        reducers[sz] = get_umap_reducer(db_feats)


    return knns,reducers

# Cell
def query_neighs(q_feat, myneighs, data, root_path, show = True):
    """
    query feature: (vector)
    myneighs:  fit knn object
    data: series or df containing "path"
    root_path:  path to image files
    """
    distance, nn_index = myneighs.kneighbors(q_feat, return_distance=True)
    dist = distance.tolist()[0]

    # fix path to the database...
    neighbors = data.iloc[nn_index.tolist()[0]].copy()
    images = [ PILImage.create(root_path/f) for f in neighbors.path]
    #PILImage.create(btn_upload.data[-1])
    if show:
        for im in images: display(im.to_thumb(IMG_SIZE,IMG_SIZE))

    return images



# Cell
def get_similar_images(paths_df,model,knns,im_sizes = IMG_SIZES,fnm=None,db=DBS['zappos'],disp=True):
    similar_images = []
    for sz in im_sizes:
        print(SIZE_ABBR[sz])
        print(im_sizes[sz])

        features = f"features_{SIZE_ABBR[sz]}"
        print(features)

        if fnm is None:
            im_path = D_ROOT/db
            fnm = im_path/QUERY_IM


        query_t = load_and_prep_sneaker(fnm,im_sizes[sz])
        query_f = get_convnet_feature(model,query_t)

        similar_images.append( query_neighs(query_f, knns[sz], paths_df, im_path, show=False) )
        if disp:
            im = PILImage.create(fnm)
            display(im.to_thumb(im_sizes[sz]))

    return similar_images


# Cell
def plot_sneak_neighs(images):
    ''' function to plot matrix of image urls.
        image_urls[:,0] should be the query image

    Args:
        images: list of lists

    return:
        null
        saves image file to directory
    '''
    nrow = len(images)
    ncol = len(images[0])

    fig = plt.figure(figsize = (20, 20))

    num=0
    for row,image_row in enumerate(images):
        for col,img in enumerate(image_row):

            plt.subplot(nrow, ncol, num+1)
            plt.axis('off')
            plt.imshow(img);

            if num%ncol == 0:
                plt.title('Query')

            if col>0:
                plt.title('Neighbor ' + str(col))
            num += 1
    plt.savefig('image_search.png')
    plt.show()



# Cell
def get_umap_embedding(latents):
    reducer = umap.UMAP(random_state=666)
    reducer.fit(latents)
    embedding = reducer.transform(latents)
    assert(np.all(embedding == reducer.embedding_))

    return embedding