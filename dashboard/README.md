# Milpa Dashboard
The Milpa Dashboard is a web UI that allows users to view the cloud costs associated with a Milpa cluster and also view the resources running on the cluster.

## Screenshots

### Cost Overview
![Cost Overview Screenshot](/screenshots/DashboardOverview.png?raw=true "Cost Overview")

### Cost Details
![Cost Details Screenshot](/screenshots/DashboardDetails.png?raw=true "Cost Details")

## Running the Dashboard
Download the dashboard manifest from github and use milpactl to create the dashboard.

```
$ wget https://raw.githubusercontent.com/elotl/milpa-apps/master/dashboard/manifests/dashboard.yml
$ milpactl create -f dashboard.yml
```

## Connecting to the Dashboard
The easiest way to connect to the running dashboard is to use `milpactl port-forward`. Find the pod name associated with the dashboard using milpactl, then setup port forwarding from the local machine.  Once port-forwarding is running you should be able to connect to the dashboard by pointing your browser at (http://localhost:5000)[http://localhost:5000]

```
$ milpactl get pods
NAME                                  UNITS     RUNNING   STATUS
milpa-dashboard-1553124938133-d1bcd   1         1         Pod Running

$ milpactl port-forward milpa-dashboard-1553124938133-d1bcd 5000
```

### Tunneling Remote Connections
If you don't have milpactl on the local machine that you'll be connecting from or milpactl can't reach the milpa master from your machine, it's pretty easy to setup ssh tunneling to a machine with milpactl and access to the milpa master.  To do this, get the address of the target machine and run the following command on the local machine.

```
# -L instructs ssh to forward the specified local port to the remote host
# -N prevents ssh from executing a command on the remote machine
$ ssh <IP/DNS address of machine with milpactl> -L 5000:localhost:5000 -N
```

### Exposing the Dashboard with a Service
As with all pods, it's possible to expose the dashboard with a service and limit access to one or more networks.

```yaml
---
kind: Service
apiVersion: v1
metadata:
  name: dashboard-svc
spec:
  selector:
    matchLabels:
      app: milpa-dashboard
  ports:
    - name: dashboard
      protocol: TCP
      port: 5000
  sourceRanges:
    - VPC
    - 10.8.0.0/16
```