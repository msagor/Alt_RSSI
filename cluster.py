import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA

#Input: list of datapoints as Pandas list, episode, min_samp_count
#Output: list of lists containing clusters
def DBSCAN_clustering_alg(X, episode, min_samp_count):

    #clustering happening here
    db_default = DBSCAN(eps = episode, min_samples = min_samp_count).fit(X) 
    labels = db_default.labels_ 

    #convert pandas list into python list
    l=X["clientRSSI"].tolist()

    #number of clusters
    n_clusters_ = len(set(labels)) #- (1 if -1 in labels else 0)
    
    #check if its only one cluster,
    #then we immediately return same list.
    if n_clusters_==1:
        #make list of list and send
        l1 = []
        l1.append(l)
        return l1
    else:
        #make list of lists to separate out the clusters
        clusters = []
        for i in range(0, n_clusters_):
            clusters.append([])

        #populate the list of lists
        for j in range(0, len(labels)):
            value = l[j]
            clusters[labels[j]-1].append(value)

        #return clusters
        return clusters


#############################main function#####################################

#load csv file and load particular column
X = pd.read_csv('files/4_7_20.csv', usecols=[1])

#clustering parameters
episode = 1
min_samp_count = 3

#do clustering
clusters = DBSCAN_clustering_alg(X, episode, min_samp_count)

#print
print("Num of clusters: " + str(len(clusters)))
for i in range(0, len(clusters)):
    print("Cluster#" + str(i) + " length: " + str(len(clusters[i])))




