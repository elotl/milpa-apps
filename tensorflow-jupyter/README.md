# Serverless Jupyter+Tensorflow

## Introduction

[Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/stable/) is a popular IDE for Machine Learning and Data Science applications.
[Tensorflow](https://www.tensorflow.org/) is a machine learning library.

This tutorial deploys Jupyter (with Tensorflow and Keras) in a nodeless fashion on Milpa.
### Step 1

Get [free Milpa Developer Edition](https://www.elotl.co/trial), install Milpa.

### Step 2

Deploy Jupyter notebook with Tensorflow and Keras libraries. Edit `tf-jupyter.yml` if you want to update `JUPYTER_TOKEN` key value. `tf-jupyter.yml` creates one Milpa deployment with one replica, and one Milpa loadbalancer service to expose our deployment.

```
# milpactl create -f tf-jupyter.yml
jupyter
jupyter
```

Wait until Jupyter pod and service are up and running. Since Jupyter container image with tensorflow+keras is large, it might take a minute for the pod to be `RUNNING`.

```
# watch milpactl get pods
Every 2.0s: milpactl get pods                                                                                        

NAME                          UNITS     RUNNING   STATUS        RESTARTS   NODE                                   IP              AGE
jupyter-1552420123567-4241m   1         1         Pod Running   0          bdd7a0da-c4ca-4b9f-b15c-4680804534ed   172.31.70.192   2m

```

Notice just-in-time provisioned, right sized instance backing Jupyter:

![JIT EC2](https://github.com/elotl/milpa-apps/blob/master/tensorflow-jupyter/screenshots/jit-jupyter-instance.png "JIT EC2")

### Step 3

Get Ingress address of Jupyter service.

```
# milpactl get svc
NAME      PORT(S)   SOURCES     INGRESS ADDRESS                                                           AGE
jupyter   80/TCP    0.0.0.0/0   milpa-rd7lediebk5pgq22y7ujcfvjkq-1682390382.us-east-1.elb.amazonaws.com   3m
```

Point your web browser to `INGRESS ADRESS`, login using `JUPYTER_TOKEN` from `tf-jupyter.yml`, create a new notebook.

![Jupyter login](https://github.com/elotl/milpa-apps/blob/master/tensorflow-jupyter/screenshots/jupyter-login.png "Jupyter login")

### Step 4

Test Tensorflow by running helloworld:

```
import tensorflow as tf

hello = tf.constant('Hello, TensorFlow!')
sess = tf.Session()
print(sess.run(hello))
```

![Tensorflow helloworld](https://github.com/elotl/milpa-apps/blob/master/tensorflow-jupyter/screenshots/tensorflow-helloworld.png "Tensorflow helloworld")

### Step 5

Tear down.

```
# milpactl delete -f tf-jupyter.yml 
jupyter
jupyter
```
