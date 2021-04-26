#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 16:23:19 2021

@author: Mick
"""
import networkx as nx
import matplotlib.pyplot as plt
from gurobipy import *
import csv
import numpy as np

# Import data, nodes first then edges
with open('SwRailPythonNodesExport.csv') as f:
    importNodes = [{k: v for k, v in row.items()}
         for row in csv.DictReader(f, skipinitialspace=True)]

with open('SwRailPythonEdgesExport.csv') as f:
    importEdges = [{k: v for k, v in row.items()}
         for row in csv.DictReader(f, skipinitialspace=True)]

# Create the model as an object
model = Model ("Minimum variance model")

# Mute the Gurobi
# model.setParam ('OutputFlag', False)

# Create the decison variables 
X = model.addVars(link_p, vtype=GRB.INTEGER, name="x")

# Balance constraints:
for i in point:
    model.addConstr(quicksum(X[i, j] for i, j in link_p.select (i, '*')) - quicksum(X[j,i] for j,i  in link_p.select ('*',i)) == 0)

# flow capacity constraints
for i ,j in link_p:
    model.addConstr(X[i, j] <= capacity_t [(i,j)])

# Define the objective function
Z = X[point[5], point[0]]
             
# Specify the type of the model: minimization or maximization
model.setObjective (Z, GRB.MAXIMIZE)

# Update the model
model.update()

# Solve the model    
model.optimize()     
        
# Print out the optimal solutions: the decion variables values
model.printAttr ('x') 

# Print out the outputs
if model.status==GRB.OPTIMAL:
    print ("-----------------------------------------")
    print ("Optimal value:",model.objVal)
    print ("-----------------------------------------")
    print ("--- flow ---")
    for i, j in link_p: 
        print ("flow From point", i, "To point", j,"is --->" ,X[i,j].X)
    