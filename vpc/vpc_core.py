import sys
from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    Stack
)

class VPCStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        vpc_cidr = self.node.try_get_context("DREAMCHASER_VPC_CIDR")
        oct_1 = vpc_cidr.split('.')[0]
        oct_2 = vpc_cidr.split('.')[1]
        total_az = len(self.availability_zones)
        sum = total_az
        exp = 0
        while sum > 0:
            sum = sum // 2
            exp = exp + 1

        pub_subnet_oct3 = 2 ** exp          # the IP address range of the public subnets for workload is from x.x.2 ** exp.0
        pri_subnet_oct3 = 2 ** exp * 4      # the IP address range of the private subnets for workload is from x.x.2 ** exp * 4.0
        iso_subnet_oct3 = 192               # the IP address range of isolated subnets is from x.x.192.0 to x.x.255.255
        ordinal_number = 0

        # creat a VPC
        self.vpc = ec2.Vpc(self, 'DREAMCHASER',
            cidr=vpc_cidr,
            max_azs=total_az, # 
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ],
            nat_gateways=1
            # uncomment the line below to create a Nat Gateway in each availability zone for high availability
            #nat_gateways=total_az
        )

        # create Public, Private and Isolated subnets in each availability zones respectivly
        for az in self.vpc.availability_zones:
            ec2.PublicSubnet(self, f"Public Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(pub_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )

            ec2.PrivateSubnet(self, f"Private Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(pri_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )

            ec2.Subnet(self, f"Isolated Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(iso_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )
            ordinal_number = ordinal_number + 1