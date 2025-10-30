import argparse
import boto3
import networkx as nx
import matplotlib.pyplot as plt

def visualize_network(region, profile, out_file):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2 = session.client("ec2")
    G = nx.DiGraph()

    # Collect VPCs, Subnets, Instances
    vpcs = ec2.describe_vpcs()["Vpcs"]
    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        G.add_node(vpc_id, label="VPC")

        subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
        for subnet in subnets:
            subnet_id = subnet["SubnetId"]
            G.add_edge(vpc_id, subnet_id, label="contains")

            instances = ec2.describe_instances(Filters=[{"Name": "subnet-id", "Values": [subnet_id]}])
            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    G.add_edge(subnet_id, instance_id, label="hosts")

    nx.draw(G, with_labels=True, node_color="lightblue", font_weight="bold")
    plt.savefig(out_file)
    print(f"✅ Network map saved as {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AWS Network Visualizer CLI")
    parser.add_argument("--region", required=True, help="AWS region, e.g., us-west-2")
    parser.add_argument("--profile", default="auto-tagger-dev", help="AWS CLI profile to use")
    parser.add_argument("--out", default="network_map.png", help="Output image file name")
    args = parser.parse_args()

    visualize_network(region=args.region, profile=args.profile, out_file=args.out)
