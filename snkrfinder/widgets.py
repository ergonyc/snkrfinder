# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/04_widgets.ipynb (unless otherwise specified).

__all__ = ['plot_umap', 'on_click_find_similar', 'find_similar', 'update_knn_reducer', 'update_model', 'dd_im_size_eh',
           'dd_model_eh', 'load_pipe', 'prep_tf_pipe', 'btn_run', 'btn_upload', 'out_umap', 'out_nn_imgs', 'dd_im_size',
           'dd_model', 'sld_sampfrac', 'knn_select', 'tab', 'cta', 'console', 'dashboard', 'console']

# Cell
#from snkrfinder.imports import *
#from snkrfinder.core import *
#from snkrfinder.data import *
from .model.core import *
from .model.transfer import *
from .model.cvae import *

#from ipywidgets import widgets
#from ipywidgets import HBox,VBox,widgets,Button,Checkbox,Dropdown,Layout,Box,Output,Label,FileUpload
# from fastai.vision.widgets import *  # in imports
#from ipywidgets import Tab #fastai didn't include Tab
import seaborn as sns


# Cell

load_pipe    = Pipeline([PILImage.create,
                         FeatsResize(size=IMG_SIZE, method='pad', pad_mode='border')] )

prep_tf_pipe = Pipeline([ToTensor(),
                         IntToFloatTensor(),
                         Normalize.from_stats(*imagenet_stats,cuda=False)])


def plot_umap(data,im_sz,mname):
    fig, ax = plt.subplots()
    sns.scatterplot(
        x="umap-one",
        y="umap-two",
        hue="Category",
        hue_order = ['Sneakers', 'Shoes', 'Boots','Slippers'],
        palette=sns.color_palette("hls", 4),
        data=data.sample(frac=sld_sampfrac.value),
        legend="full",
        alpha=0.3,ax=ax
    )
    ax.set_aspect('equal', 'datalim')
    ax.set_title(f'UMAP projection of {mname} embedded UT-Zappos data (sz={IMG_SIZES[im_sz]})', fontsize=12)
    return ax

def on_click_find_similar(change):
    """
    this is the 'go' signal
    """
    global im_sz
    update_knn_reducer(im_sz)
    find_similar()

def find_similar():
    """
    find the knn
    """
    global knns,model,im_sz,df
    neighs = knns[im_sz]

    # load the image
    im = btn_upload.data[-1]
    img = load_pipe(im)
    tensor_im = prep_tf_pipe(img)
    feats = get_convnet_feature(model, tensor_im)

    # find the neighbors
    distance, nn_index = neighs.kneighbors(feats.numpy(), return_distance=True)
    dist = distance.tolist()[0]
    # fix path to the database...
    neighbors = df.iloc[nn_index.tolist()[0]].copy()
    nbr = neighbors.index


    #widget(im, max_width="292px")

    images = [ PILImage.create(D_ROOT/DBS['zappos']/f) for f in neighbors.path]

    ts = [VBox([widget(im, max_width="292px"),Label(f"d={d:.03f}")]) for im,d in zip(images,dist)]
    target_im = img.to_thumb(200,200)

    car_nn = carousel(ts, width='1200px')

    out_nn_imgs.clear_output()
    with out_nn_imgs:
        display(HBox([widget(target_im, max_width="500px"), car_nn]))

    #lbl_neighs.value = f'distances: {dist}


def update_knn_reducer(size):
    "update knn & reducer for new size im, but nothing is recalculated until the btn_run is clicked"
    # set to the current
    global model,knns,reducers,im_sz,df
    im_sz = size

    umap = reducers[im_sz]
    neighs = knns[im_sz]

    features = f"features_{SIZE_ABBR[im_sz]}"
    data = df[['Category',features]].copy()

    db_feats = np.vstack(data[features].values)
    # this is probably the bottleneck...
    embedding = umap.transform(db_feats)
    data['umap-one'] = embedding[:,0]
    data['umap-two'] = embedding[:,1]

    out_umap.clear_output()
    with out_umap:
        ax = plot_umap(data,size,model.name)
        plt.show(ax)

    find_similar()

def update_model(model_name,size):
    " update the model but nothing is recalculated until the btn_run is clicked"
    #key = {sz:i for (i,sz) in enumerate(IMG_SIZES)}
    global model,knns,reducers,df
    model = MODELS[model_name]

    num_neighs = 5
    if model_name!=model.name :  print(f"dammit, '{model_name}'!='{model.name}'")
    # save the knns and umap reducers for later use
    knns = load_pickle(f"data/{model.name}-knn{num_neighs}Xsize.pkl")

    reducers = load_pickle(f"data/{model.name}-umapXsize.pkl")

    filename = f"zappos-50k-{model.name}-features_sort_3"
    df = pd.read_pickle(f"data/{filename}.pkl")

    update_knn_reducer(size)

#Events
def dd_im_size_eh(change):
    update_knn_reducer(change.new)

def dd_model_eh(change):
    update_model(change.new,dd_im_size.value)


#define my widgets
btn_run = Button(description='Find similar sneaks!',layout = Layout(width='25%', height='80px'))
btn_upload = FileUpload(layout = Layout(width='25%', height='80px'))

out_umap = Output() # not doing anything here yet...
# lbl_neighs = Label() # labels for neighbors
out_nn_imgs = Output() # VBox([out_im,out_car])

dd_im_size = Dropdown(options=IMG_SIZES.keys(),value='small',description='Image Size:' )
dd_model = Dropdown(options=['mobilenet_v2','resnet18'],
                    value='mobilenet_v2',
                    disabled=False,
                    description='Model:')
                    #,layout = Layout(width='40%') ) #style=style,

sld_sampfrac = widgets.FloatSlider(value=.5,
                min=0,
                max=1.0,
                step=0.05,
                description='sample %:',
                disabled=False,
                continuous_update=False,
                orientation='vertical',
                readout=True,
                readout_format='.2f',
)

#item_layout = widgets.Layout(margin='0 0 50px 0')
#input_widgets = widgets.HBox([dd_model, dd_im_size])

knn_select = HBox([dd_model, dd_im_size])


tab = widgets.Tab(children=[out_nn_imgs,HBox([out_umap, sld_sampfrac]) ] )#,layout=item_layout)
tab.set_title(0, 'Dataset Exploration')
tab.set_title(1, 'UMAP Plot')

cta = HBox([widgets.Label('Find your sneaker!    '),
            btn_upload,
            btn_run])

console = Label()
dashboard =  VBox([ cta,
                    knn_select,
                    tab,
                  console])

console = Label()
# actions
btn_run.on_click(on_click_find_similar)
dd_im_size.observe(dd_im_size_eh, names='value')
dd_model.observe(dd_model_eh, names='value')
# dd_lat_dim.observe(dd_lat_dim_eh, names='value')

