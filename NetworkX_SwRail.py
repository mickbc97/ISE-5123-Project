#05/03/2016 - Master's Thesis - Mackenzie Whitman

#Modified from NetworkX_multicommodity.py
#Import SwRail data generated from SwRail_Redistribute_Source_Sink.m
#Add super source/sink to networkx
#visualize and prepare to export to optimization model

import networkx as nx
import matplotlib.pyplot as plt
from gurobipy import *
import csv
import numpy as np
from copy import deepcopy

# Import data, nodes first then edges
with open('SwRailMatlabNodesExport.csv') as f:
    importNodes = [{k: v for k, v in row.items()}
         for row in csv.DictReader(f, skipinitialspace=True)]

with open('SwRailMatlabEdgesExport.csv') as f:
    importEdges = [{k: v for k, v in row.items()}
         for row in csv.DictReader(f, skipinitialspace=True)]

#Create networkx graph from data
G = nx.DiGraph()

#loop through imported nodes, convert data type, add to graph and set node attributes
#modified 04/19/2016 - use search feature to loop through keys and lump together demand, inflow, pos, and supply

#true/false boolean for assigning commodity count
commodityCounted = False

for i in importNodes:
    natt = {}
    
    #convert node to integer value, if is not an integer, just use string identifier (1 vs 'STM')
    try:
        n = int(i['node'])
        
    except ValueError:
        n = i['node']
        
    batchInflow = []
    batchPos = []
    station = str(i['station'])
    
    
    #use search to look for demand dict keys, lump together, then combine in demand list
    for j in sorted(i.keys()):
        if 'inflow' in j:
            batchInflow.append(j)
        elif 'pos' in j:
            batchPos.append(j)
            
    if commodityCounted == False:
        N = len(batchInflow)
        commodityCounted = True
            
    myorder = [0 for x in range(len(batchInflow))]

    #sort batchInflow before looping
    for j in range(len(batchInflow)):
        x = int(batchInflow[j].split("_")[-1]) - 1
        myorder[x] = j
        
    batchInflow = [batchInflow[x] for x in myorder]

    #loop through batches combine in dictionaries, update graph
    bd = []
    for j in batchInflow:
        if bool(i[j]):
            bd.append(int(i[j]))
    if not bd:
        bd = [0 for x in range(len(batchInflow))]
    natt['inflow'] = bd
    
    bp = []
    for j in batchPos:
        if bool(i[j]):
            bp.append(i[j])
    if bp:        
        natt['pos'] = bp       

    G.add_node(n, natt)
    
#create arcij and arcji, with same capacity and cost for both    
for i in importEdges:
    #attempt to convert to integer for node id, but convert to string if doesn't work
    try:
        ai = int(i['arc_i'])
    except ValueError:
        ai = i['arc_i']
    try:
        aj = int(i['arc_j'])
    except ValueError:
        aj = i['arc_j']
    
    arcij = (ai, aj)

    batchCapacity = []
    
    for j in sorted(i.keys()):
        if 'capacity' in j:
            batchCapacity.append(j)
            
    myorder = [0 for x in range(len(batchCapacity))]
                
    #sort batchCapacity before looping
    for j in range(len(batchCapacity)):
        x = int(batchCapacity[j].split("_")[-1]) - 1
        myorder[x] = j
        
    batchCapacity = [batchCapacity[x] for x in myorder]    

    bc = []
    for j in batchCapacity:
        bc.append(int(i[j]))
    
    G.add_edge(*arcij)
    
    cap = {arcij: bc}
    nx.set_edge_attributes(G, 'capacity', cap)
    
#create super source/sink per commodity k
#modified from NetworkX_multicommodity.py
# 05/03/2016

#N assigned from len(batchInflow)
#two columns of sink/sources
steps = (0.2E+6)/(N/2)
posy1 = np.arange(7.2E+6, 7.4E+6, steps)
posy1 = np.repeat(posy1, 2)
posy2 = np.arange(6.8E+6, 7.0E+6, steps)
posy2 = np.repeat(posy2, 2)
posx1 = np.array([3.5E+5, 3.75E+5])
posx1 = np.resize(posx1, N)
posx2 = np.array([9.0E+5, 9.25E+5])
posx2 = np.resize(posx2, N)

pos1 = zip(posx1, posy1)
pos2 = zip(posx2, posy2)

#keep track of super sink/source variable names 
supSourceNames = []
supSinkNames = []

#intialize inflow = [0] of size N 
initflow = [0 for x in range(N)]

#create super source/sink nodes, add to networkX
for i in range(N):
    supSource = {'pos': pos1[i], 'inflow': initflow, 'supply': initflow}
    supSink = {'pos': pos2[i], 'inflow': initflow, 'demand': initflow}
    
    if i < 10:
        G.add_node("superSource0{0}".format(i), supSource)
        G.add_node("superSink0{0}".format(i), supSink)
        
        #keep track of source/sink names
        supSourceNames.append("superSource0{0}".format(i))
        supSinkNames.append("superSink0{0}".format(i))        
        
    else:
        G.add_node("superSource{0}".format(i), supSource)
        G.add_node("superSink{0}".format(i), supSink)
    
        #keep track of source/sink names
        supSourceNames.append("superSource{0}".format(i))
        supSinkNames.append("superSink{0}".format(i))
    
    

inflow = deepcopy(nx.get_node_attributes(G, 'inflow'))

#for each commodity, see if node is sink/source
for k in range(N):
    
    #loop through sources and sinks in G, add inflow/arc to superSource or superSink
    for i, j in inflow.iteritems():
        #if > 0, then supply
        if j[k] > 0:
            #add supply from node to super source to exisiting supply
            x = G.node[supSourceNames[k]]['inflow']
            #only want commodity specfic inflow data (set all other commodity inflows = 0)
            y = [0 for z in range(N)]
            y[k] = j[k]
            z = [a+b for a,b in zip(x,y)]
            G.node[supSourceNames[k]]['inflow'] = z
            
            x = G.node[supSourceNames[k]]['supply']
            y = [0 for z in range(N)]
            y[k] = j[k]
            z = [a+b for a,b in zip(x,y)]
            G.node[supSourceNames[k]]['supply'] = z
            
            #set capacity of new arc = supply at supply node
            #modification 04/21/2016 y[N] must equal the capacity, for summing
            #modification 05/04/2016, must create two arcs, bidirectional, for SwRail data
            #constraints of optimization model will take care of capacity, so just make two copies            
            y = [0 for z in range(N+1)]
            y[k] = j[k]
            y[N] = j[k]
            cap = {'capacity':y}
            
            #create new arc from supply node to super source
            G.add_edge(i, supSourceNames[k], cap)
            G.add_edge(supSourceNames[k], i, cap)
            
        #if <0, then demand     
        if j[k] < 0:
            #add demand from node to super sink
            x = G.node[supSinkNames[k]]['inflow']
            #only want commodity specfic inflow data (set all other commodity inflows = 0)
            y = [0 for z in range(N)]
            y[k] = j[k]
            z = [a+b for a,b in zip(x,y)]
            G.node[supSinkNames[k]]['inflow'] = z
            
            x = G.node[supSinkNames[k]]['demand']
            y = [0 for z in range(N)]
            y[k] = j[k]
            z = [a+b for a,b in zip(x,y)]
            G.node[supSinkNames[k]]['demand'] = z
            
            #set capacity of new arc = demand at demand node
            #modification 04/21/2016 y[N] must equal the capacity, for summing
            #modification 05/04/2016, must create two arcs, bidirectional, for SwRail data
            #constraints of optimization model will take care of capacity, so just make two copies
            y = [0 for z in range(N+1)]
            y[k] = -j[k]
            y[N] = -j[k]
            cap = {'capacity':y}
            
            #create new arc from demand node to super source
            G.add_edge(i, supSinkNames[k], cap)
            G.add_edge(supSinkNames[k], i, cap)
            
#node list data, (supply, demand, position, inflow)
nodeList = deepcopy(G.node)

#edge list data (capacity)
edgeList = deepcopy(nx.to_edgelist(G))

Nodes = []
Edges = []

#modify edgeList to list of dictionairies for each edge, individual capacities
for i in edgeList:
    edge = {'arc_i': i[0], 'arc_j': i[1]}
    cap = i[2]['capacity']
    for j in  range(len(cap)):
        if j < 10:
            capDict = {"capacity_0{0}".format(j): cap[j]}
            edge.update(capDict)            
        else:
            capDict = {"capacity_{0}".format(j): cap[j]}
            edge.update(capDict)
    
    
    Edges.append(edge)

#modify nodeList to list of dictionairies for each edge, inflow, etc.

#nested dictionairies must be unpacked before exporting
for key, value in nodeList.iteritems():
    node = {'node':key}
    for i, j in value.iteritems():
        for k in range(len(j)):
            if k < 10:
                node["{0}_0{1}".format(i,k)] =j[k]
            else:
                node["{0}_{1}".format(i,k)] =j[k]
                 
    Nodes.append(node)

#write data to csv file for future use
with open("SwRailPythonEdgesExport2.csv", "wb") as f:
    keys = sorted(set().union(*(d.keys() for d in Edges)))
    writer = csv.DictWriter(f, keys)
    writer.writeheader()
    writer.writerows(Edges)



#two fields associated with the dictionary position, needs to be rewritten    
with open("SwRailPythonNodesExport2.csv", "wb") as f:
    keys = sorted(set().union(*(d.keys() for d in Nodes)))
    writer = csv.DictWriter(f, keys)
    writer.writeheader()
    writer.writerows(Nodes)
    
    
    
# # Visualize network, Good luck soldier, modified from NetworkX_multicommodity
# pos = nx.get_node_attributes(G, 'pos')


# #create plot for each commodity
# for k in range(N):
#     #show inflow data for commodity k, no other commodity
#     #modification 05/04/2016 size nodes,
#     allP = deepcopy(nx.get_node_attributes(G, 'inflow'))
#     p = {}
    
    
#     for i,j in allP.iteritems():
#         if j[k] > 0:
#             p[i] = 1
#         elif j[k] < 0:
#             p[i] = -1
#         else:
#             p[i] = 0
    
#     #show edges for commodity k, no other commodity, 
#     # 05/04/2016 - don't plot edges from source/sink nodes
#     allE = deepcopy(nx.get_edge_attributes(G, 'capacity'))
#     e = []
    
#     for i,j in allE.iteritems():
#         ss = False
#         for sup in supSinkNames:
#             if i[0] == sup:
#                 ss = True
#                 break
#             elif i[1] == sup:
#                 ss = True
#                 break
#         for sup in supSourceNames:
#             if i[0] == sup:
#                 ss = True
#                 break
#             elif i[1] == sup:
#                 ss = True
#                 break
#         if ss == False:
#             e.append(i)
            
        
    
#     plt.figure(figsize=(11,8.5))
#     drawEdges = nx.draw_networkx_edges(G,pos, e, alpha=0.4)
#     drawNodes = nx.draw_networkx_nodes(G,pos,nodelist=p.keys(),
#                            node_size=40,
#                            node_color=p.values(),
#                            label = 'Inflow',
#                            cmap=plt.cm.Reds_r)
    
#     pos2 = {}
#     for key, value in pos.iteritems():
#         x, y = value
#         pos2[key] = [x + 0.01, y + 0.01]
    
#     #nx.draw_networkx_labels(G, pos2)
    
#     cbar = plt.colorbar(drawNodes, ticks = [-1, 0, 1], label = 'Inflow')
#     cbar.ax.set_yticklabels(['Sink', 'Network', 'Source'])
#     plt.xlim(-2E+5, 14E+5)
#     plt.ylim(6E+6,7.8E+6)
    
#     mng = plt.get_current_fig_manager()
#     #mng.window.state('zoomed')
    
    
#     #manager = plt.get_current_fig_manager()
#     #manager.resize(*manager.window.maxsize())    
    
    
    
    
#     #plt.savefig('SwRailNetwork_{0}.png'.format(k))
#     #plt.show()

