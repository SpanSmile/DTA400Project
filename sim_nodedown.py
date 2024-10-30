import simpy
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Global list to store successful hops
successful_hops = {}
lenght = 1000 
seed = 42
num_nodes = 8
down_node_index = random.randint(0, num_nodes - 1)

class Packet:
    def __init__(self, src, dst, id):
        self.src = src
        self.dst = dst
        self.id = id
        self.done = 999  # Flag to indicate whether the packet is done or not
        self.hops_left = 0  # Count of hops to reach the destination via left direction
        self.hops_right = 0  # Count of hops to reach the destination via right direction

class Node:
    def __init__(self, env, id, ring_size):
        self.env = env
        self.id = id
        self.ring_size = ring_size
        self.neighbors = []  # Neighbors in the ring
        self.stp = False  # Set to True when STP is enabled
        self.down = False  # Set to True if the node is down
        self.env.process(self.run())  # Start the process for this node

    def run(self):
        while True:
            yield self.env.timeout(1)  # Wait 1 second between actions (can be adjusted)

    def set_neighbors(self, left_neighbor, right_neighbor):
        """Set the neighbors for the ring topology."""
        self.neighbors = [left_neighbor, right_neighbor]

    def send(self, packet):
        """Send a packet to the destination by broadcasting it around the ring."""
        if self.down:
            print(f"Node {self.id} is down. Packet {packet.id} cannot be sent.")
            return  # Prevent sending from a down node
        
        print(f"Node {self.id} sending packet {packet.id} to Node {packet.dst}")
        
        # Broadcast to both neighbors
        if self.neighbors:  # Check if there are neighbors
            # Forward to the right neighbor
            yield self.env.process(self.forward(packet, True))
            # Forward to the left neighbor
            yield self.env.process(self.forward(packet, False))

    def forward(self, packet, direction):
        """Forward the packet to the next node in the ring."""
        if self.id == packet.dst and self.down == False:
            hops = packet.hops_right if direction else packet.hops_left
            if hops > 0:
                if hops < packet.done:
                    packet.done = hops
                    print(f"Packet {packet.id} arrived at destination {self.id} with {hops} hops.")
                    successful_hops[packet.id] = hops
                else:
                    print("Packet already delivered")
            else:
                hops += 1
                if hops < packet.done:
                    packet.done = hops
                    print(f"Packet {packet.id} arrived at destination {self.id} with {hops} hops.")
                    successful_hops[packet.id] = hops
                else:
                    print("Packet already delivered")
            return  # Stop forwarding, we've reached the destination

        # If this node is down, it can still receive the packet but won't forward it
        if self.down:
            print(f"Node {self.id} is down but nothing happen to packet {packet.id}.")
            return  # Stop forwarding, as this node is down

        # Increment hop count based on direction
        if direction:  # Right direction
            packet.hops_right += 1
        else:  # Left direction
            packet.hops_left += 1

        # Determine the next node based on direction
        next_node = self.neighbors[1] if direction else self.neighbors[0]
        print(f"Node {self.id} forwarding packet to Node {next_node.id}.")
        yield self.env.timeout(0.1)  # Simulate network delay
        yield self.env.process(next_node.forward(packet, direction))  # Correctly yield the forwarding process

class FiberRingNetwork:
    def __init__(self, env, num_nodes):
        self.env = env
        self.nodes = [Node(env, i, num_nodes) for i in range(num_nodes)]

        # Connect the nodes in a ring
        for i in range(num_nodes):
            left_neighbor = self.nodes[(i - 1) % num_nodes]
            right_neighbor = self.nodes[(i + 1) % num_nodes]
            self.nodes[i].set_neighbors(left_neighbor, right_neighbor)

        # Randomly select one node to be down
        #down_node_index = 1
        self.nodes[down_node_index].down = True
        print(f"Node {down_node_index} is down and will not send packets.")

    def send_packet(self, src, dst, i):
        """Send a packet from source node to destination node."""
        # Prevent the source from being the down node
        if self.nodes[src].down:
            print(f"Cannot send from down node {src}. Selecting a different source.")
            return None  # No packet is sent from down node
        packet = Packet(src, dst, i)
        return self.nodes[src].send(packet), packet  # Return the generator process and the packet

    def print_network_topology(self):
        """Print out the neighbors of each node in the ring."""
        print("\nNetwork Topology:")
        for node in self.nodes:
            left_neighbor = node.neighbors[0].id if node.neighbors else None
            right_neighbor = node.neighbors[1].id if node.neighbors else None
            print(f"Node {node.id}: Left Neighbor = Node {left_neighbor}, Right Neighbor = Node {right_neighbor}, STP = {'Enabled' if node.stp else 'Disabled'}, Down = {'Yes' if node.down else 'No'}")
        print("")

# Simulation setup
def run_simulation():
    #random.seed(seed)
    env = simpy.Environment()
    network = FiberRingNetwork(env, num_nodes)

    # Print the network topology before running the simulation
    network.print_network_topology()
    # Send multiple packets (e.g., 10 packets from various sources to various destinations)
    for i in range(lenght):
        src = random.randint(0, num_nodes - 1)
        dst = random.randint(0, num_nodes - 1)
        while src == down_node_index:  # Ensure the destination is not the same as the source
            src = random.randint(0, num_nodes - 1)
        while dst == src:  # Ensure the destination is not the same as the source
            dst = random.randint(0, num_nodes - 1)

        packet_process, packet = network.send_packet(src, dst, i)
        env.process(packet_process)
    #packet_process, packet = network.send_packet(7, 0, 0)
    #env.process(packet_process)
        
    env.run(until=10)  # Run for a longer time to allow more packets to be processed

    # Prepare data for plotting
    print(f"Successful Hops: {successful_hops}")
    # Check if successful_hops is not empty before plotting
    if successful_hops:
        # Extract hop values from the dictionary
        hop_counts = list(successful_hops.values())
    
        # Calculate average, min, and max hops
        avg_hops = np.mean(hop_counts)
        min_hops = np.min(hop_counts)
        max_hops = np.max(hop_counts)
    
        # Count of successful hops
        successful = len(successful_hops)
        
        print(f"Sent: {lenght}, Success: {successful}, Percentage: {(successful/lenght) * 100}%") 
        print(f"Average Hops: {avg_hops:.2f}, Min Hops: {min_hops}, Max Hops: {max_hops}")
    
        # Create a histogram plot in a separate figure
        plt.figure(figsize=(10, 6))
        plt.hist(hop_counts, bins=range(max(hop_counts) + 2), align='left', color='blue', alpha=0.7)
        plt.title('Distribution of Successful Hop Counts to Destination')
        plt.xlabel('Hops')
        plt.ylabel('Number of Packets Reaching Destination')
    
        # Ensure y-axis ticks are integers
        ax1 = plt.gca()
        ax1.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        plt.xticks(range(max(hop_counts) + 1))
        plt.grid(axis='y')
    
        plt.tight_layout()
        plt.show()  # Show the histogram plot
    
        # Create a bar chart for hops statistics in another figure
        plt.figure(figsize=(10, 6))
        plt.bar(['Average Hops', 'Minimum Hops', 'Maximum Hops'],
                [avg_hops, min_hops, max_hops], color=['green', 'orange', 'red'])
        plt.title('Hops Statistics')
        plt.ylabel('Number of Hops')
    
        # Ensure y-axis ticks are integers
        ax2 = plt.gca()
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        plt.grid(axis='y')
    
        plt.tight_layout()
        plt.show()  # Show the hops statistics plot
    
        # Create a bar chart for sent and successful packets in another figure
        plt.figure(figsize=(10, 6))
        plt.bar(['Sent Packets', 'Successful Packets'],
                [lenght, successful], color=['blue', 'purple'])
        plt.title('Sent/Successful Packets')
        plt.ylabel('Number of Packets')
    
        # Ensure y-axis ticks are integers
        ax3 = plt.gca()
        ax3.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        plt.grid(axis='y')
    
        plt.tight_layout()
        plt.show()  # Show the sent/successful packets plot
    
    else:
        print("No packets reached their destination.")


run_simulation()
