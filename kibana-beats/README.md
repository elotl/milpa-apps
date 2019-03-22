# Serverless Kibana, Beats

## Introduction

[Kibana](https://www.elastic.co/products/kibana) is a popular visualiasation plugin for Elasticsearch. [Beats](https://www.elastic.co/products/beats) are lightweight data shippers to Elasticsearch and Logstash. Kibana and Beats are stateless, hence are ideal workloads to run in a serverless fashion using Milpa.

This tutorial deploys Milpa, Kibana, Beats on AWS. The tutorial deploys Elasticsearch in `single-node` mode to provide Kibana and Beats data to work off of. If you'd like to deploy Elasticsearch in a serverless fashion using Milpa, [please contact Elotl]().

### Step 1

[Get free Milpa Developer Edition](https://www.elotl.co/trial), install Milpa.

### Step 2

a) Deploy Elasticsearch in `single-node` mode. If you are curious, look through `elasticsearch.yml` to see how it is configured.

```
# milpactl create -f elasticsearch.yml 
elasticsearch
elasticsearch
```

b) Deploy Kibana with Metricbeat. `kibana.yml` is configured to run Kibana unit with Metricbeat. Lets create Kibana deployment and expose it via Ingress service.

```
# milpactl create -f kibana.yml
kibana
kibana
```

c) Deploy Nginx with Filebeat to ship access and error logs to Elasticseach.

```
# milpactl create -f nginx.yml 
nginx
nginx
```

### Step 3

Wait for Elasticsearch, Kibana (with Metricbeat), Nginx (with Filebeat) to be available (`RUNNING` state).

```
# watch milpactl get pods
Every 2.0s: milpactl get pods                                                                Fri Mar 22 00:11:02 2019

NAME                         UNITS     RUNNING   STATUS        RESTARTS   NODE                                   IP
            AGE
elasticsearch                1         1         Pod Running   0          1034bee8-492a-4701-974e-f690953ab75f   172.
31.74.185   2m
kibana-1553213347531-ppgbs   2         2         Pod Running   0          99c60028-ae76-40b8-a9e5-2d2b911408d7   172.
31.64.75    1m
nginx-1553213357407-2zj9v    2         2         Pod Running   0          fdcf303e-bb5d-4d2d-b861-a1354ef0b11a   172.
31.69.253   1m

```

Checkout EC2 console, filter by `tag` set to `nginx`, `elasticsearch`, `kibana`, notice just-in-time provisioned right-sized nodes for our deployments.
![EC2 JIT](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/ec2-jit.png "EC2 JIT")

### Step 4

Get the ingress address of Kibana.

```
milpactl get svc kibana
NAME      PORT(S)   SOURCES     INGRESS ADDRESS                                                           AGE
kibana    80/TCP    0.0.0.0/0   milpa-tptzek4l2xdbirxgcunq5vbwq4-2145047121.us-east-1.elb.amazonaws.com   2m
```

### Step 5

Access Kibana dashboard using `INGRESS ADDRESS`. Check out Kibana Pod Metrics delivered by Metricbeat.

![Kibana](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/kibana-1.png "Kibana")

### Step 6


Get Ingress Address of Nginx, then generate workload for Nginx.
```
# milpactl get svc nginx
NAME      PORT(S)   SOURCES     INGRESS ADDRESS                                                          AGE
nginx     80/TCP    0.0.0.0/0   milpa-xfladrzkzcndvfbc2xqip3ed6e-879954594.us-east-1.elb.amazonaws.com   12m

# ./curl-servers.sh milpa-xfladrzkzcndvfbc2xqip3ed6e-879954594.us-east-1.elb.amazonaws.com:80
```

Look at Nginx access logs on Kibana!
![Nginx logs](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/nginx-filebeat-logs.png "Nginx logs")

### Step 7

Tear down.

a) Terminate `curl-servers.sh` process.

b) Terminate Elasticsearch, Kibana, Nginx deployments.

```
# milpactl delete -f elasticsearch.yml 
elasticsearch
elasticsearch

# milpactl delete -f kibana.yml 
kibana
kibana

# milpactl delete -f nginx.yml 
nginx
nginx
```

Verify that your underlying EC2 instances with `app:nginx`, `app:kibana`, `app:elasticsearch` tags have disappeared.

![EC2 after](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/ec2-after.png "ec2-after")

## Coming soon

Elasticsearch Instance Store support

## Questions/comments

Please file and issue or reach out to Elotl at info@elotl.co .
