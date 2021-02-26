# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02c_model.cvae.ipynb (unless otherwise specified).

__all__ = ['prep_df_for_datablocks', 'df_get_x', 'df_get_y', 'get_ae_btfms', 'LatentTuple', 'TensorPoint',
           'Tensor2Vect', 'LatentsTensor', 'LatentTupleBlock', 'LatentsTensorBlock', 'df_ae_x', 'df_ae_y',
           'get_ae_DataBlock', 'ReparamTricker', 'VAELinear', 'VAELayer', 'VAEBottleneck', 'UpsampleBlock', 'VAE_rnet',
           'BVAELoss', 'MyMetric', 'MSEMetric', 'RawKLDMetric', 'BWeightedKLDMetric', 'MuMetric', 'MuSDMetric',
           'StdSDMetric', 'StdMetric', 'KLWeightMetric', 'AnnealedLossCallback', 'bn_splitter', 'resnetVAE_split',
           'trns_mobilenet_v2', 'VAE_mnet', 'bn_splitter', 'mnetV2_split', 'AE_rnet', 'AE_mnet']

# Cell
#from snkrfinder.imports import *
#from snkrfinder.core import *
#from snkrfinder.data import *
from .core import *
#from snkrfinder.model.transfer import *

from fastai.test_utils import show_install, synth_learner, nvidia_smi, nvidia_mem

# Cell

def prep_df_for_datablocks(df):
    df = df[["path","train","test","validate","t_t_v"]].copy()
    # I could remove all the "test" rows... for now i'll choose an alternate strategy:
    # Drop all the "test" rows for now, and create an "is_valid" column...
    # should probably drop a ton of columns to jus tkeep the file paths...
    # just keep what we'll need below
    df.loc[:,'is_valid'] = df.test | df.validate
    return df



# Cell

# some helper functions borrowed from validating the feature embedding
def df_get_x(r):
    return image_path/r['path']

def df_get_y(r):
    # we want to return a tuple so that we predict latent variables...
    return (df_get_x(r),None,None)

# Cell
def get_ae_btfms():
    batch_tfms = Normalize.from_stats(*imagenet_stats)
    rand_tfms = aug_transforms(mult=1.0,
               do_flip=True,
               flip_vert=False,
               max_rotate=3.0,
               min_zoom=.95,
               max_zoom=1.0,
               max_lighting=0.1,
               max_warp=0.023,
               p_affine=0.66,
               p_lighting=0.2,
               xtra_tfms=None,
               size=None,
               mode='bilinear',
               pad_mode='border',
               align_corners=True,
               batch=False,
               min_scale=1.0)
    return rand_tfms+[batch_tfms]

# Cell

class LatentTuple(fastuple):
    "Basic type for tuple of tensor (vectors)"
    _show_args = dict(s=10, marker='.', c='r')
    @classmethod
    def create(cls, ts):
        if isinstance(ts,tuple):
            mu,logvar = ts
        elif ts is None:
            mu,logvar = None,None
        else:
            mu = None
            logvar = None

        if mu is None: mu = torch.empty(0)
        elif not isinstance(mu, Tensor): Tensor(mu)

        if logvar is None: logvar = torch.empty(0)
        elif not isinstance(logvar,Tensor): Tensor(logvar)

        return cls( (mu,logvar) )


    def show(self, ctx=None, **kwargs):
        mu,logvar = self
        if not isinstance(mu, Tensor) or not isinstance(logvar,Tensor): return ctx

        title_str = f"mu-> {mu.mean():e}, {mu.std():e}  logvar->{logvar.mean():e}, {logvar.std():e}"

        if 'figsize' in kwargs: del kwargs['figsize']
        if 'title' in kwargs: kwargs['title']=title_str
        if ctx is None:
            _,axs = plt.subplots(1,2, figsize=(12,6))
            x=torch.linspace(0,1,mu[0].shape[0])
            axs[0].scatter(x, mu[:], **{**self._show_args, **kwargs})
            axs[1].scatter(x, logvar[:], **{**self._show_args, **kwargs})
            ctx = axs[1]

        ctx.scatter(mu[:], logvar[:], **{**self._show_args, **kwargs})
        return ctx





class TensorPoint(TensorBase):
    "Basic type for points in an image"
    _show_args = dict(s=10, marker='.', c='r')

    @classmethod
    def create(cls, t, img_size=None)->None:
        "Convert an array or a list of points `t` to a `Tensor`"
        return cls(tensor(t).view(-1, 2).float(), img_size=img_size)

    def show(self, ctx=None, **kwargs):
        if 'figsize' in kwargs: del kwargs['figsize']
        x = self.view(-1,2)
        ctx.scatter(x[:, 0], x[:, 1], **{**self._show_args, **kwargs})
        return ctx


class Tensor2Vect(TensorPoint): pass

class LatentsTensor(Tensor2Vect):
    "Basic type for latents as Tensor inheriting from TensorPoint (vectors)"
    @classmethod
    def create(cls, ts, img_size=IMG_SIZE):
        "create IMG_SIZE attr to register plotting..."

        if isinstance(ts,tuple):
            mu,logvar = ts
        elif ts is None:
            mu,logvar = None,None
        else:
            mu = None
            logvar = None
        if mu is None: mu = torch.empty(0)
        elif not isinstance(mu, Tensor): Tensor(mu)

        if logvar is None: logvar = torch.empty(0)
        elif not isinstance(logvar,Tensor): Tensor(logvar)

        t = torch.cat([mu,logvar],dim=-1) # in case its a batch?

        return cls(tensor(t).view(-1, 2).float(), img_size=img_size)

#     def show(self, ctx=None, **kwargs):
#         if 'figsize' in kwargs: del kwargs['figsize']
#         x = self.view(-1,2)
#         ctx.scatter(x[:, 0], x[:, 1], **{**self._show_args, **kwargs})
#         return ctx
#         mu,logvar = self
#         if not isinstance(mu, Tensor) or not isinstance(logvar,Tensor): return ctx

#         title_str = f"mu-> {mu.mean():e}, {mu.std():e}  logvar->{logvar.mean():e}, {logvar.std():e}"

#         if 'figsize' in kwargs: del kwargs['figsize']
#         if 'title' in kwargs: kwargs['title']=title_str
#         if ctx is None:
#             _,axs = plt.subplots(1,2, figsize=(12,6))
#             x=torch.linspace(0,1,mu[0].shape[0])
#             axs[0].scatter(x, mu[:], **{**self._show_args, **kwargs})
#             axs[1].scatter(x, logvar[:], **{**self._show_args, **kwargs})
#             ctx = axs[1]

#         ctx.scatter(mu[:], logvar[:], **{**self._show_args, **kwargs})
#         return ctx


# Cell
# could we do a typedispatch to manage the transforms...?
# def VAETargetTupleBlock():
#     return TransformBlock(type_tfms=VAETargetTuple.create, batch_tfms=IntToFloatTensor)

def LatentTupleBlock():
    return TransformBlock(type_tfms=LatentTuple.create, batch_tfms=noop)


def LatentsTensorBlock():
    return TransformBlock(type_tfms=LatentsTensor.create, batch_tfms=noop)


def df_ae_x(r):
    return image_path/r['path']


# need to make sure that we get the image whihc is "Identical" to the input.. how to test?
# lambda o: o
def df_ae_y(r):
    # we want to return a tuple so that we predict latent variables...
    return df_get_x(r)


# Cell
# is simplgy grabbing Y as an identical datablock right?
def get_ae_DataBlock():
    "wrapper to get the standard ae datablock"
    block = DataBlock(blocks=(ImageBlock(cls=PILImage), ImageBlock(cls=PILImage), LatentsTensorBlock ),
              get_x=df_ae_x,
              get_y=[df_ae_y, noop], #don't need to get the LatentsTensorBlock, just create
              splitter=ColSplitter('is_valid'),
              item_tfms= Resize(IMG_SIZE,method='pad', pad_mode='border'),
              batch_tfms = get_ae_btfms() ,
              n_inp = 1)

    return block




# Cell

# this is the "Variational" magic.  aka the "reparamaterization trick"
class ReparamTricker(Module):
    def forward(self,mu,logvar):
        if True: #self.training:
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            z = mu + eps * std
            return z
        else:
            return mu

class VAELinear(Module):
    def __init__(self,in_features,latent_features):
        self.fc_in = LinBnDrop(in_features,latent_features,bn=True,p=0.0,act=nn.ReLU(),lin_first=False)
        self.mu_linear = nn.Linear(latent_features,latent_features)
        self.logvar_linear = nn.Linear(latent_features,latent_features)

    def forward(self,x):
        h = self.fc_in(x)
        mu = self.mu_linear(h)
        logvar = self.logvar_linear(h)
        return mu,logvar


class VAELayer(Module):
    def __init__(self,in_features,latent_features):
        self.mu_logvar = VAELinear(in_features,latent_features)
        self.reparam = ReparamTricker()

    def forward(self,h):
        mu,logvar = self.mu_logvar(h)
        #logvar = F.softplus(logvar)   # force logvar>0
        z = self.reparam(mu,logvar) # adds the noise by the reparam trick
        return z, mu, logvar


class VAEBottleneck(Module):
    def __init__(self,input_dim,fc_dim,latent_dim,bn=True,drop_p=0.0,act=nn.ReLU()):
        self.bn = nn.Sequential(LinBnDrop(input_dim,fc_dim,bn=False),
                        VAELayer(in_features=fc_dim, out_features=latent_dim))

    def forward(self,h):
        # maybe assert that the shape is bs,encoder_features?
        z,mu,logvar = self.bn(h)
        return z, mu, logvar

# Cell
class UpsampleBlock(Module):
    def __init__(self, up_in_c:int, final_div:bool=True, blur:bool=False, leaky:float=None, **kwargs):
        """
        up_in_c :  "Upsample input channel"
        """
        self.shuf = PixelShuffle_ICNR(up_in_c, up_in_c//2, blur=blur, **kwargs)
        ni = up_in_c//2
        nf = ni if final_div else ni//2
        self.conv1 = ConvLayer(ni, nf, **kwargs) # since we'llapply it by hand...
        self.conv2 = ConvLayer(nf, nf, **kwargs)

    def forward(self, up_in:Tensor) -> Tensor:
        up_out = self.shuf(up_in)
        return self.conv2(self.conv1(up_out))

    def shuff(self,up_in:Tensor) -> Tensor:
        up_out = self.shuf(up_in)
        cat_x = self.relu(up_out)
        return cat_x


# Cell

class VAE_rnet(Module):
    def __init__(self,bs=32, enc_dim=512, latent_dim=128, im_size=IMG_SIZE,out_range=[-3,3],pretrained=True):
        #  drop_p=0.0 default turns off dropout

        self.im_size=im_size
        # encoder

        arch,cut = xresnet18(pretrained=True),-4
        self.encoder = nn.Sequential(*list(arch.children())[:cut],
                                   Flatten())

        base_d = 5 #img_size//(2**5) = img_size//32
        self.in_dim = enc_dim * base_d**2  # 2**(3*3) * (im_size//32)**2 #(output of resneet) #12800
        # Sampling vector
        self.latent_dim = latent_dim

        n_blocks = 5
        self.bn = VAELayer(self.in_dim,self.latent_dim)

        fc_out = LinBnDrop(latent_dim,im_size*n_blocks*n_blocks,bn=False,p=0.0,act=nn.ReLU(),lin_first=True)

        nfs = [3] + [2**i*n_blocks for i in range(n_blocks+1)]
        nfs.reverse()
        n = len(nfs)

        modules =  [UpsampleBlock(nfs[i]) for i in range(n - 2)]
        self.decoder = nn.Sequential(fc_out,
                                ResizeBatch(im_size,n_blocks,n_blocks),
                                *modules,
                                ConvLayer(nfs[-2],nfs[-1],
                                                ks=1,padding=0, norm_type=None,
                                                #act_cls=nn.Sigmoid) )
                                             act_cls=partial(SigmoidRange, *out_range)))

    def decode(self, z):
        z = self.decoder(z)
        return z

    def reparam(self, h):
        return self.bn(h)

    def encode(self, x):
        h = self.encoder(x)
        z, mu, logvar = self.reparam(h)
        return z, mu, logvar

    def forward(self, x):
        z, mu, logvar = self.encode(x)
        x_hat = self.decode(z)
        latents = torch.stack([mu,logvar],dim=-1)
        return x_hat, latents # assume dims are [batch,latent_dim,concat_dim]

# Cell

# called `after_batch`
class BVAELoss(Module):
    """
    Measures how well we have created the original image,
    plus the KL Divergence with the unit normal distribution
    """
    def __init__(self, im_size, latent_dim, b_weight=None):
        mse = MSELossFlat(reduction='sum')
        if b_weight is None:
            # normalize to the mse and KLD have equalized magnitudes.
            #  we are summing over number of pixels and latent dimension
            b_weight = BETA * (3*im_size*im_size)/latent_dim #
            # make small (mse ~ 1000*KLD) to start beta balancing the two losses
        store_attr('mse,im_size,latent_dim,b_weight')

    def forward(self, preds, *target):
        """
        pred =(x_hat,KLD,kl_weight) #mu,log_var, kl_weight)
        target is x (original)
        """

        # this handles the annealed kl_weight and passing the mu,logvar around we added...
        if(len(preds) == 3):
            x_hat, latents, kl_weight = preds
        else: #if len(preds) == 2:  # we should never get here...
            x_hat, latents = preds

            kl_weight = x_hat[0].new(1)
            kl_weight[0] = 1.0

        #mu,logvar = latents[:,:,0],latents[:,:,1]
        mu, logvar = latents.split(1,dim=2)

        #note: both mse and KLD are summing errors over batches, and pixels or latents
        total = self.mse(x_hat, target[0])

        KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        KLD = KLD.sum()*kl_weight

        return (total + self.b_weight*KLD)



# Cell

# test: if i call them preds instead of vals might the Metric base class reset automatically?
class MyMetric(Metric):
    "for simple average over batch quantities"
    def reset(self):
        "Clear all targs and preds"
        self.vals = []
    @property
    def value(self):
        return np.array(self.vals).mean()

class MSEMetric(MyMetric):
    def __init__(self):
        self.vals= []
    def accumulate(self, learn):
        x_hat = learn.pred[0]
        x_targs = learn.y[0]
        self.vals.append(  to_detach( F.mse_loss(x_hat, x_targs, reduction='sum') ))

class RawKLDMetric(MyMetric):
    def __init__(self):
        self.vals = []
    def accumulate(self, learn):
        latents = learn.pred[1]
        mu, logvar = latents.split(1,dim=2)
        KLD =  -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        self.vals.append(to_detach(KLD))

class BWeightedKLDMetric(MyMetric):
    def __init__(self,im_size,latent_dim):
        self.vals = []
        self.b_weight = BETA*(3.*im_size*im_size)/latent_dim
    def accumulate(self, learn):
        latents = to_detach(learn.pred[1])
        mu, logvar = latents.split(1,dim=2)

        # _,mu,logvar = to_detach(learn.pred)
        b_weight = self.b_weight/mu.shape[0]
        KLD = b_weight * -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        self.vals.append( KLD )


class MuMetric(MyMetric):
    def __init__(self): self.vals = []
    def accumulate(self, learn):
        latents = to_detach(learn.pred[1])
        mu, logvar = latents.split(1,dim=2)
        self.vals.append(to_detach(mu.mean()))


class MuSDMetric(MyMetric):
    def __init__(self): self.vals = []
    def accumulate(self, learn):
        latents = to_detach(learn.pred[1])
        mu, logvar = latents.split(1,dim=2)
        self.vals.append(to_detach(mu.std()))


class StdSDMetric(MyMetric):
    def __init__(self): self.vals = []
    def accumulate(self, learn):
        latents = to_detach(learn.pred[1])
        mu, logvar = latents.split(1,dim=2)
        self.vals.append(to_detach((logvar).std()))


class StdMetric(MyMetric):
    def __init__(self): self.vals = []
    def accumulate(self, learn):
        latents = to_detach(learn.pred[1])
        mu, logvar = latents.split(1,dim=2)
        self.vals.append(to_detach((logvar.exp_() ** .5).mean()))


class KLWeightMetric(MyMetric):
    def __init__(self): self.vals = []
    def accumulate(self, learn):
        #kl = learn.model.kl_weight
        kl = learn.opt.hypers[0]['kl_weight']
        #KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        self.vals.append(kl)


# Cell

class AnnealedLossCallback(Callback):
    def after_pred(self):
        kl = self.learn.pred[0].new(1)
        kl[0] = self.opt.hypers[0]['kl_weight']
        self.learn.pred = self.learn.pred + (kl,)
    def after_batch(self):
        pred, latents, _ = self.learn.pred
        self.learn.pred = (pred,latents)


# Cell

# note that it is crucial that you don't freeze the batch norm layers...
def bn_splitter(m):
    def _bn_splitter(l, g1, g2):
        if isinstance(l, nn.BatchNorm2d): g2 += l.parameters()
        elif hasattr(l, 'weight'): g1 += l.parameters()
        for ll in l.children(): _bn_splitter(ll, g1, g2)

    g1,g2 = [],[]
    _bn_splitter(m[0], g1, g2)

    g2 += m[1:].parameters()
    return g1,g2

def  resnetVAE_split(m):
    to_freeze, dont_freeze = bn_splitter(m.encoder)
    #return L(to_freeze, dont_freeze + params(m.bn)+params(m.dec[:2]), params(m.dec[2:]))
    return L(to_freeze, dont_freeze + params(m.bn)+params(m.decoder))
    #return L(fz, nofz + params(m.bn)+params(m.dec[:6]), params(m.dec[6:]))



# Cell
def trns_mobilenet_v2():
    model_conv = torchvision.models.mobilenet_v2(pretrained=True)
    for param in model_conv.parameters():
        param.requires_grad = False
    # Parameters of newly constructed modules have requires_grad=True by default
    # just read this off: model_conv.classifier
    num_ftrs = model_conv.classifier._modules['1'].in_features
    model_conv.classifier._modules['1'] = nn.Linear(num_ftrs, num_categories)

    return model_conv

# check enc_dim...
class VAE_mnet(Module):
    def __init__(self,bs=32, latent_dim=128, im_size=IMG_SIZE,out_range=[-3,3],pretrained=True):
        #  drop_p=0.0 default turns off dropout, removed enc_dim=512

        self.im_size=im_size
        # encoder


        # need to make the mnet and cut here...
        arch,cut = torchvision.models.mobilenet_v2(pretrained=True),-1
        enc_dim = arch.classifier._modules['1'].in_features

        self.enc = nn.Sequential(*list(arch.children())[:cut],
                                   Flatten())


        base_d = 5 #img_size//(2**5) = img_size//32
        self.in_dim = enc_dim * base_d**2  # 2**(3*3) * (im_size//32)**2 #(output of resneet) #12800
        # Sampling vector
        self.latent_dim = latent_dim


        n_blocks = 5
        self.bn = VAELayer(self.in_dim,self.latent_dim)

        fc_out = LinBnDrop(latent_dim,im_size*n_blocks*n_blocks,bn=False,p=0.0,act=nn.ReLU(),lin_first=True)

        nfs = [3] + [2**i*n_blocks for i in range(n_blocks+1)]
        nfs.reverse()
        n = len(nfs)

        modules =  [UpsampleBlock(nfs[i]) for i in range(n - 2)]
        self.dec = nn.Sequential(fc_out,
                                 ResizeBatch(im_size,n_blocks,n_blocks),
                                *modules,
                                ConvLayer(nfs[-2],nfs[-1],
                                                ks=1,padding=0, norm_type=None,
                                                #act_cls=nn.Sigmoid) )
                                             act_cls=partial(SigmoidRange, *out_range)))
        #error parameters
        self.mu = Tensor([bs,latent_dim])
        self.logvar =  Tensor([bs,latent_dim])


    def reparam(self, h):
        z, mu, logvar = self.bn(h)
        self.mu = mu
        self.logvar = logvar

        return z

    def forward(self, x):
        h = self.enc(x)
        z = self.reparam(h)
        x_reconst = self.dec(z)

        return x_reconst #, z, mu, logvar

# Cell

# note that it is crucial that you don't freeze the batch norm layers...
def bn_splitter(m):
    def _bn_splitter(l, g1, g2):
        if isinstance(l, nn.BatchNorm2d): g2 += l.parameters()
        elif hasattr(l, 'weight'): g1 += l.parameters()
        for ll in l.children(): _bn_splitter(ll, g1, g2)

    g1,g2 = [],[]
    _bn_splitter(m[0], g1, g2)

    g2 += m[1:].parameters()
    return g1,g2

def mnetV2_split(m):
    to_freeze, dont_freeze = bn_splitter(m.enc)
    #return L(to_freeze, dont_freeze + params(m.bn)+params(m.dec[:2]), params(m.dec[2:]))
    return L(to_freeze, dont_freeze + params(m.bn)+params(m.dec))
    #return L(fz, nofz + params(m.bn)+params(m.dec[:6]), params(m.dec[6:]))



# Cell

class AE_rnet(Module):
    def __init__(self,bs=32, enc_dim=512, latent_dim=128, im_size=IMG_SIZE,out_range=[-3,3],pretrained=True):
        #  drop_p=0.0 default turns off dropout

        self.im_size=im_size
        # encoder

        arch,cut = xresnet18(pretrained=True),-4
        self.enc = nn.Sequential(*list(arch.children())[:cut],
                                   Flatten())


        base_d = 5 #img_size//(2**5) = img_size//32
        self.in_dim = enc_dim * base_d**2  # 2**(3*3) * (im_size//32)**2 #(output of resneet) #12800
        # Sampling vector
        self.latent_dim = latent_dim


        n_blocks = 5
        #         self.bn = VAELayer(self.in_dim,self.latent_dim)
        fc_in = LinBnDrop(self.in_dim,latent_dim,bn=False,p=0.0,act=nn.ReLU(),lin_first=True)
        fc_out = LinBnDrop(latent_dim,im_size*n_blocks*n_blocks,bn=False,p=0.0,act=nn.ReLU(),lin_first=True)

        nfs = [3] + [2**i*n_blocks for i in range(n_blocks+1)]
        nfs.reverse()
        n = len(nfs)

        modules =  [UpsampleBlock(nfs[i]) for i in range(n - 2)]
        self.dec = nn.Sequential(fc_in,
                                 fc_out,
                                 ResizeBatch(im_size,n_blocks,n_blocks),
                                 *modules,
                                 ConvLayer(nfs[-2],nfs[-1],
                                                ks=1,padding=0, norm_type=None,
                                                #act_cls=nn.Sigmoid) )
                                             act_cls=partial(SigmoidRange, *out_range)))


    def forward(self, x):
        h = self.enc(x)
        x_reconst = self.dec(h)

        return x_reconst #, z, mu, logvar

# Cell

# # deterministic autoencoder...
# rnet_ae = nn.Sequential(rnet_body, rnet_dec)


# check enc_dim...
class AE_mnet(Module):
    def __init__(self,bs=32, latent_dim=128, im_size=IMG_SIZE,out_range=[-3,3],pretrained=True):
        #  drop_p=0.0 default turns off dropout, removed enc_dim=512

        self.im_size=im_size
        # encoder


        # need to make the mnet and cut here...
        arch,cut = torchvision.models.mobilenet_v2(pretrained=True),-1
        enc_dim = arch.classifier._modules['1'].in_features

        self.enc = nn.Sequential(*list(arch.children())[:cut],
                                   Flatten())


        base_d = 5 #img_size//(2**5) = img_size//32
        self.in_dim = enc_dim * base_d**2  # 2**(3*3) * (im_size//32)**2 #(output of resneet) #12800
        # Sampling vector
        self.latent_dim = latent_dim


        n_blocks = 5
        self.bn = VAELayer(self.in_dim,self.latent_dim)

        fc_out = LinBnDrop(latent_dim,im_size*n_blocks*n_blocks,bn=False,p=0.0,act=nn.ReLU(),lin_first=True)

        nfs = [3] + [2**i*n_blocks for i in range(n_blocks+1)]
        nfs.reverse()
        n = len(nfs)

        modules =  [UpsampleBlock(nfs[i]) for i in range(n - 2)]
        self.dec = nn.Sequential(fc_out,
                                 ResizeBatch(im_size,n_blocks,n_blocks),
                                *modules,
                                ConvLayer(nfs[-2],nfs[-1],
                                                ks=1,padding=0, norm_type=None,
                                                #act_cls=nn.Sigmoid) )
                                             act_cls=partial(SigmoidRange, *out_range)))
        #error parameters
        self.mu = Tensor([bs,latent_dim])
        self.logvar =  Tensor([bs,latent_dim])


    def reparam(self, h):
        z, mu, logvar = self.bn(h)
        self.mu = mu
        self.logvar = logvar

        return z

    def forward(self, x):
        h = self.enc(x)
        z = self.reparam(h)
        x_reconst = self.dec(z)

        return x_reconst #, z, mu, logvar
