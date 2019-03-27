# Serverless Elasticsearch, Kibana, and Beats

## Introduction

Logging is a vital component of any production system.  Milpa makes it easy to collect application and system logs, ship them to a centralized logging server and visualize those logs for further analysis and alerting.  In this tutorial we'll use Milpa, [Elasticsearch](https://www.elastic.co/products/elasticsearch), [Beats](https://www.elastic.co/products/beats) and [Kibana](https://www.elastic.co/products/kibana) to quickly build out the logging infrastrucuture for a Milpa cluster.  Along the way, we'll demonstrate how to setup local disk storage (Instance Store) on a virtual machine for fast and cost effective storage of logging data.

### Step 1: Install Milpa

[Request a free Milpa Community Edition license](https://www.elotl.co/trial), and [install Milpa](https://static.elotl.co/docs/latest/doc.html#installation).

### Step 2: Start the Services

In this example, we'll deploy Elasticsearch on Milpa in `single-node` mode on a r5d.large instance. The r5d machines are a good match for our use case since they have extra memory and fast local NVMe drives attached to the instance.  To make use of the locally attached storage, we'll need to do a bit of work to format and mount the disk before starting elasticsearch.  In `elasticsearch.yml` we use an `initUnit` (shown below) to format the attached drive and mount it into a directory shared with the elasticsearch unit. 

```yaml
  - name: formatter
    image: ubuntu:bionic
    command: ["/bin/sh", "-c"]
    args: ["mkfs.ext4 -O ^has_journal /dev/nvme0n1 && mkdir /data/storage && mount /dev/nvme0n1 /data/storage -o noatime,nodiratime,barrier=0; chmod 777 /data/storage"]
    volumeMounts:
    - mountPath: /data
      name: shared-volume
```

Since it's a best-practice to avoid pet servers, we don't plan on rebooting the elasticsearch instance or expect it to survive a power failure or similar disaster.  As such, we've chosen to increase the disk's performance by disabling journaling and write barriers. After taking a look at the manifest, create the elasticsearch pod and service in Milpa:

```bash
$ milpactl create -f elasticsearch.yml 
elasticsearch
elasticsearch
```

We'll Deploy Nginx with Filebeat and Metricbeat to ship logs and metrics to Elasticseach. In this tutoral, Nginx simply serves as an example source of logging information.

```bash
$ milpactl create -f nginx.yml 
nginx
nginx
```

Finally we'll deploy Kibana with Metricbeat. `kibana.yml` is configured to run a Kibana unit with Metricbeat tracking the metrics of the pod.  Create the Kibana deployment and expose it via a load balancer service.

```bash
$ milpactl create -f kibana.yml
kibana
kibana
```

### Step 3: Wait for Running

Wait for Elasticsearch, Kibana, and Nginx to be running (`STATUS` == `Pod Running`).

```bash
$ watch milpactl get pods
Every 2.0s: milpactl get pods                                                                Fri Mar 22 00:11:02 2019

NAME                         UNITS     RUNNING   STATUS        RESTARTS   NODE           IP
elasticsearch                1         1         Pod Running   0          1034bee8-...   172...
kibana-1553213347531-ppgbs   2         2         Pod Running   0          99c60028-...   172...
nginx-1553213357407-2zj9v    2         2         Pod Running   0          fdcf303e-...   172...
```

To see what has happened behind the scenes, navigate to the EC2 console, filter by `tag` set to `nginx`, `elasticsearch`, and `kibana`.  You'll see just-in-time provisioned right-sized nodes for our deployments.
![EC2 JIT](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/ec2-jit1.png "EC2 JIT")

### Step 4: Kibana

Get the ingress address of Kibana by querying the `kibana` service.

```bash
milpactl get svc kibana
NAME      PORT(S)   SOURCES     INGRESS ADDRESS                                                           AGE
kibana    80/TCP    0.0.0.0/0   milpa-tptzek4l2xdbirxgcunq5vbwq4-2145047121.us-east-1.elb.amazonaws.com   2m
```

Plug the Kibana dashboard `INGRESS ADDRESS` into a web browser. In the Infrastructure UI you should be able to see the Kibana Pod Metrics delivered by Metricbeat.

![Kibana](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/kibana-1.png "Kibana")

### Step 6: Logs

Lets start generating a bit of traffic for nginx.  Get the Ingress Address of Nginx and use curl-servers.sh to generate a small sample workload for Nginx.
```bash
$ milpactl get svc nginx
NAME      PORT(S)   SOURCES     INGRESS ADDRESS                                                          AGE
nginx     80/TCP    0.0.0.0/0   milpa-xfladrzkzcndvfbc2xqip3ed6e-879954594.us-east-1.elb.amazonaws.com   12m

$ ./curl-servers.sh milpa-xfladrzkzcndvfbc2xqip3ed6e-879954594.us-east-1.elb.amazonaws.com:80
```

In the Logs UI of Kibana, we can see the Nginx access logs delivered to elasticsearch.
![Nginx logs](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/nginx-filebeat-logs.png "Nginx logs")

### Step 7: Teardown
That's all there is to it!  We've successfully walked through setting up elasticsearch and related systems to generate and view logs and metrics.  All of this was done using Milpa instead of building out servers manually.  Since we're done with this demonstration, lets delete the pods and services:

a) Terminate the `curl-servers.sh` process with a `Ctrl-C`

b) Delete the Elasticsearch, Kibana and Nginx pods and services:

```bash
$ milpactl delete -f elasticsearch.yml 
elasticsearch
elasticsearch

$ milpactl delete -f kibana.yml 
kibana
kibana

$ milpactl delete -f nginx.yml 
nginx
nginx
```

Verify that your underlying EC2 instances with `app:nginx`, `app:kibana`, `app:elasticsearch` tags have disappeared.

![EC2 after](https://github.com/elotl/milpa-apps/blob/master/kibana-beats/screenshots/ec2-after.png "ec2-after")

## Further Work: Reliability
The elasticsearch cluster we setup has no long-term durability. If the instance gets terminated or there are disk problems, the cluster data will be lost. While we could run a larger, replicated cluster and hope we don't experience parallel failures, a simpler and more cost-effective solution is to periodically snapshot and backup the cluster to cloud storage. Lucky for us there are [Elasticsearch plugins](https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html) that take care of the snapshot and restore from cloud storage.  Snapshotting is a great way to ensure durability for a cluster that can tolerate a small window of data loss in the event of a disaster. We've used snapshotting to great success in our work at Elotl and at other companies.

## Questions/comments

If you have questions or comments, feel free to reach out to Elotl at info@elotl.co or file an issue in this repo.
