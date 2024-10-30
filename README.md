DTA400 Project - Ring Network Topology Simulation with SimPy
This project contains two simulations that model a ring network topology using the SimPy library. Both simulations represent different network scenarios, with the goal of studying how messages propagate across nodes in a ring topology, especially when using the Spanning Tree Protocol (STP) to prevent loops.

Project Overview
sim.py: This simulation models a basic ring network with nodes that send messages in a circular fashion. Each run involves a randomly selected sender and destination node, with STP enabled on random nodes in the ring.

sim_nodedown.py: This simulation runs the same ring network but with one node down, meaning STP is completely disabled.
