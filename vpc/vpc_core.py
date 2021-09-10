import sys
from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ram as ram,
    Stack, Tags
)

class VPCStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def vpc(self, vpc_cidr):    
        vpc_cidr = vpc_cidr
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
        iso_subnet_oct3 = 160               # the IP address range of isolated subnets is from x.x.192.0 to x.x.255.255
        db_subnet_oct3 = 192
        tgw_subnet_oct3 = 240
        ordinal_number = 0
        self.route_tables = []
        self.tgw_subnets = []
        self.db_subnets = []

        self.vpc = ec2.Vpc(self, 'VPC',
            cidr=vpc_cidr,
            max_azs=total_az,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ],
            nat_gateways= total_az if self.node.try_get_context("DREAMCHASER_VPC_HA") else 1
        )

        # create Public, Private, Database, Isolated and tgw subnets in each availability zones respectivly
        for az in self.vpc.availability_zones:
            public_subnet = ec2.PublicSubnet(self, f"Public Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(pub_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )
            public_subnet.add_default_internet_route(self.vpc.internet_gateway_id, self.vpc.internet_connectivity_established)
            self.route_tables.append(public_subnet.route_table.route_table_id)

            private_subnet = ec2.PrivateSubnet(self, f"Private Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(pri_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )
            self.route_tables.append(private_subnet.route_table.route_table_id)

            db_subnet = ec2.Subnet(self, f"Database Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(db_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )

            isolated_subnet = ec2.Subnet(self, f"Isolated Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(iso_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )

            tgw_subnet = ec2.Subnet(self, f"TGW Subnet Zone {az}",
                cidr_block='.'.join((oct_1, oct_2, str(tgw_subnet_oct3 + ordinal_number), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=az
            )
            self.tgw_subnets.append(tgw_subnet.subnet_id)
            ordinal_number = ordinal_number + 1

        #self.apply_endpoint(vpc_id=self.vpc.vpc_id, rt_ids=route_tables)

    def apply_endpoint(self, vpc_id: str, rt_ids: list) -> None:
        ec2.CfnVPCEndpoint(self, "VPCEnpoint",
            service_name="com.amazonaws." + self.region + ".s3",
            vpc_id=vpc_id,
            route_table_ids=rt_ids,
            vpc_endpoint_type="Gateway",
            policy_document = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": [
                                "s3:GetObject",
                                "s3:ListBucket",
                                "s3:ListObjects"
                            ],
                            "Resource": [
                                f"arn:aws:s3:::amazoncloudwatch-agent-{self.region}/*",
                                f"arn:aws:s3:::patch-baseline-snapshot-{self.region}/*",
                                f"arn:aws:s3:::amazon-ssm-{self.region}/*",
                                f"arn:aws:s3:::aws-ssm-{self.region}/*",
                                f"arn:aws:s3:::{self.region}-birdwatcher-prod/*",
                                f"arn:aws:s3:::prod-{self.region}-starport-layer-bucket/*"
                            ]
                        }
                    ]
                }
        )

    def create_tgw(self):
        self.tgw = ec2.CfnTransitGateway(self, "TGW",
            amazon_side_asn=65000,
            auto_accept_shared_attachments='enable',
            default_route_table_association='disable',
            default_route_table_propagation='disable',
            dns_support='enable',
            vpn_ecmp_support='enable'
        )

    # share your transit gateway in your aws organization
    def share_tgw(self, ou_id: str, tgw_id: str) -> None:
        ram.CfnResourceShare(self, 'RAMTgw',
            name='dc_one_ou_id',
            principals=[ou_id],
            resource_arns=[f"arn:aws:ec2:{self.region}:{self.account}:transit-gateway/{tgw_id}"]
        )

    def create_tgw_attach(self, vpc_id: str, tgw_id: str, tgw_subnets: str):
        self.tgw_attach = ec2.CfnTransitGatewayAttachment(self, "TGWAttach",
            subnet_ids=tgw_subnets,
            transit_gateway_id=tgw_id,
            vpc_id=vpc_id
        )

    def create_tgw_route(self, tgw_id: str, asso_tgw_attach_id: str, dest_tgw_attach_id: str, dest_cidr: str):
        self.tgw_rt = ec2.CfnTransitGatewayRouteTable(self, "TGWRt",
            transit_gateway_id=tgw_id
        )

        self.tgw_rt_asso = ec2.CfnTransitGatewayRouteTableAssociation(self, "TGWRtAssociation",
            transit_gateway_attachment_id=asso_tgw_attach_id,
            transit_gateway_route_table_id=self.tgw_rt.ref
        )

        self.tgw_route = ec2.CfnTransitGatewayRoute(self, "TGWRoute",
            transit_gateway_route_table_id=self.tgw_rt.ref,
            destination_cidr_block=dest_cidr,
            transit_gateway_attachment_id=dest_tgw_attach_id,

        )

    # create vpc in dreamchaser way easily
    def dc_easy_vpc(self):
        self.vpc(vpc_cidr=self.node.try_get_context('DC_VPC_CIDR'))
        self.apply_endpoint(vpc_id=self.vpc.vpc_id, rt_ids=self.route_tables)
        self.create_tgw()
        self.create_tgw_attach(vpc_id=self.vpc.vpc_id, tgw_id=self.tgw.ref, tgw_subnets=self.tgw_subnets)
        
    # Tags.of(self.vpc).add("DREAMCHASER", "DREAMCHASERVPC")

    # self.vpc.from_lookup(self, 'MYVPC',
    #     tags = { "DREAMCHASER": "DREAMCHASERVPC" }
    # )