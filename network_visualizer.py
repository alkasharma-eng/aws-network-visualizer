import boto3
import networkx as nx
import matplotlib.pyplot as plt

def visualize_network(region='us-west-2'):
    ec2 = boto3.client('ec2', region_name=region)
    G = nx.DiGraph()

    vpcs = ec2.describe_vpcs()['Vpcs']
    for vpc in vpcs:
        vpc_id = vpc['VpcId']
        G.add_node(vpc_id, label='VPC')

        subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
        for subnet in subnets:
            subnet_id = subnet['SubnetId']
            G.add_edge(vpc_id, subnet_id, label='contains')

            instances = ec2.describe_instances(Filters=[{'Name': 'subnet-id', 'Values': [subnet_id]}])
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    G.add_edge(subnet_id, instance_id, label='hosts')

    nx.draw(G, with_labels=True, node_color='lightblue', font_weight='bold')
    plt.savefig('network_map.png')
    print("✅ Network map saved as network_map.png")

if __name__ == "__main__":
    visualize_network()
