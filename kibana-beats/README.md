# Work In Progress

## Serverless Kibana, Beats

## Introduction

[Kibana](https://www.elastic.co/products/kibana) is a popular visualiasation plugin for Elasticsearch. [Beats](https://www.elastic.co/products/beats) are lightweight data shippers to Elasticsearch and Logstash. Kibana and Beats are stateless, hence are ideal workloads to run in a serverless fashion using Milpa.

This tutorial deploys Milpa, Kibana, Beats on AWS. The tutorial deploys Elasticsearch in `single-node` mode to provide Kibana and Beats data to work off of. If you'd like to deploy Elasticsearch in a serverless fashion using Milpa, [please contact Elotl]().

### Step 1

Get free Milpa Developer Edition, install Milpa.

### Step 2

Deploy Elasticsearch in `single-node` mode. If you are curious, look through `elasticsearch.yml` to see how it is configured.

```
# milpactl create -f elasticsearch.yml 
elasticsearch
elasticsearch
```

### Step 3

Deploy Kibana, Metricbeat. `kibana.yml` is configured to run Kibana unit with Metricbeat. Lets create Kibana deployment and expose it via Ingress service.

```
# milpactl create -f kibana.yml
kibana
kibana
```

### Step 4

Wait for Elasticsearch, Kibana, Metricbeat to be available (`RUNNING` state).

```
# watch milpactl get pods
Every 2.0s: milpactl get pods                                                                           Wed Mar  6 00:07:38 2019

NAME                         UNITS     RUNNING   STATUS        RESTARTS   NODE                                   IP
 AGE
elasticsearch                1         1         Pod Running   0          89f89214-0d81-4728-8f09-ef24b03503a2   172.31.77.23
 3m
kibana-1551830753319-n05tp   2         2         Pod Running   0          7b535505-9840-4f11-8ad9-372c63517c12   172.31.68.235
 1m
```

### Step 5

Get the ingress address of Kibana.

```
# milpactl get svc kibana
NAME      PORT(S)   SOURCES     INGRESS ADDRESS                                                           AGE
kibana    80/TCP    0.0.0.0/0   milpa-tptzek4l2xdbirxgcunq5vbwq4-1057411873.us-east-1.elb.amazonaws.com   2m
```

### Step 6

Access Kibana dashboard using `INGRESS ADDRESS`. Check out Kibana Pod Metrics delivered by Metricbeat.

Inline-style: 
![Kibana pod metrics 1](https://github.com/elotl/milpa-apps/tree/master/kibana-beats/screenshots/kibana1.png "Kibana pod metrics 1")
![Kibana pod metrics 2](https://github.com/elotl/milpa-apps/tree/master/kibana-beats/screenshots/kibana2.png "Kibana pod metrics 2")

### Step 7

Lets scale Kibana deployment from 1 pod up to 3 pods!

```
```

### Step 8

Lets check out Kibana deployment metrics from Kibana dashboard. We should now see metrics from 3 Metricbeats from the 3 Kibana pods!

Lets also look at our EC2 console page for all EC2 instances with `app:kibana` tags. We should now see 2 new right sized EC2 instances corresponding to the 2 new pods spun up during scale up.

### Step 9

Interested in a serverless standalone Beat that is not colocated with any pod? Deploy heartbeat pod to see how that will work. Heartbeat is configured to ping two http services: `elasticsearch` service we deployed in Step 2, and `www.google.com`.

```
```

### Step 10

From Kibana dashboard's discover tab, we should now see hearbeats from `elasticsearch` service and `www.google.com`.

### Step 11

Tear down.

```
```


