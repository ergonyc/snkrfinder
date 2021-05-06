# Welcome to `snkrfinder`
> this repository / module are used to develop the fastai API version of Sneaker Finder:  a tool to help find sneakers similar to what you like!


This file will become your README and also the index of your documentation.


### version 0.2.4 Feb 2021 (0.1 Insight tf/keras)

## OVERVIEW - WIP

This is a full refactor of the Sneaker Finder tool I developed as an initial Insight Data Science sprint project.  The original project used TensorFlow, Keras, and Flask.  This project has been completely rewritten with the fastai API and pytorch.  The primary goal was to provide a task to learn pytorch and the fastai api, but I also aim to compose several blogs.

This is a project initiated while an Insight Data Science fellow.  It grew out of my interest in making data driven tools in the fashion/retail space I had most recently been working.   The original over-scoped idea was to make a shoe desighn tool which could quickly develop some initial sneakers based on choosing some examples, and some text descriptors.  Designs are constrained by the "latent space" defined (discovered?) by a database of shoe images.  However, given the 3 week sprint allowed for development, I pared the tool down to a simple "aesthetic" recommender for sneakers, using the same idea of utilizing an embedding space defined by the database fo shoe images.


## Install

`pip install snkrfinder`

installs the snkrfinder module...
- snkrfinder.core -> snkrfinder (utils)

- snkrfinder.data -> snkrfinder.data.munge

- snkrfinder.model -> snkrfinder.model (.core .cvae .transfer)

- snkrfinder.widget -> snkrfinder.widget.feats



NOTE:  symbolic link in the nbs directory to enable the module loads in these notebooks.  i.e. `ln -s ../snkrfinder/ snkrfinder`


## How to use

Fill me in please! Don't forget code examples:

```
1+1
```




    2



dump_pickle[source]
dump_pickle(filepath, item_to_save)

simple wrapper to load a pickelfile

```
HOME
```




    Path('/home/ergonyc')


