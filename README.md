# k8s-disruption-shuffler

This repo contains a helm chart to periodically delete and recreate  
pod disruptionbudgets to allow the cluster autoscaler to scale 
thecluster down after businesshours without beeing blocked by 
restrictive budgets.

## function
The helm charts creates two cron jobs the dirsuptor and the 
reconstructor which run a pod, that queries the k8s api and list all
pdb (pod disruption budget) that have a certain set of labels. Cerain
namespaces can be excluded.

The disruptor cronjob than fetches all selected pdbs and stores away
a templated representation of the pdv inside the state config map.
It then deltes all selected pdbs

The reconstructor reads in all pdb definitions from the state configmap
and recreates all pdbs.

## fighting-pit
To fuel the religious war about which is the best programming language, 
the container used go, python and rust implementations of the container
code to provide totally non representative comparison between them. 
