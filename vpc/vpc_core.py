import sys
import uuid
import time
import hashlib
from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ram as ram,
    Stack, Tags, CfnJson, IResolvable
)

class VPCStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def add_vpc(self, vpc_cidr: str, enable_internet: bool, enable_nat: bool, vpc_ha: bool=False, vpc_endpoint: bool=False) -> None:
        """
        Add an AWS VPC

        Scenarios:
            1. VPC with both inbound and outbound internet connectivity. E.g. single AWS VPC environment; or for
            provisioning the VPC as the outbound VPC for the other VPCs in your organization.
                - set both the arguments "enable_internet" and "enable_nat" to True   
            2. VPC with direct inbound internet connectivity. But its outbound internet connectivity goes via
            outbound VPC. E.g. VPCs on an AWS member account which connects to a transit gateway that is attached
            to a VPC dedicated for outbound internet connectivity.
                - set the argument "enable_internet" to True; and set the argument "enable_nat" to False
            3. VPC WITHOUT direct inbound internet connectivity; however, it has outbound internet connectivity 
            via a VPC which has direct outbound internet connectivity. Without adding any routes via any gateway,
            resource in this type of VPC is self-isolated completely.
                - set both the arguments "enable_internet" and "enable_nat" to False
            4. To implement network level high availability for tolerating AWS zone level service down on the VPC
            with direct outbound internet connectivity.
                - set both the arguments "enable_nat" and "vpc_ha" to True. By default, only a single AWS NatGatewy is
                implemented in the first availability zone(zone A) of the designated AWS region.

        Args:
            vpc_cidr (str): the Classless Inter-Domain Routing for AWS VPC.
            enable_internet (bool): set to True to enable inbound internet connectivity.
            enable_nat (bool): set to True to enable outbound internet connectivity via VPC NatGateway.
            vpc_ha (bool): set to True to provision multiple VPC NatGateway for high availability.
            vpc_endpoint: set to True to connect to supported AWS services via AWS PrivateLink.
        """
        self.vpc_cidr = vpc_cidr
        self.oct_1 = self.vpc_cidr.split('.')[0]
        self.oct_2 = self.vpc_cidr.split('.')[1]
        self.enable_internet = enable_internet
        self.enable_nat = enable_nat
        self.vpc_ha = vpc_ha
        self.vpc_endpoint = vpc_endpoint
        self.nat_gateway_ids = []
        if self.enable_internet or self.enable_nat:
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        else:
            subnet_configuration=[]

        self.vpc = ec2.Vpc(self, 'VPC',
            cidr=self.vpc_cidr,
            max_azs=len(self.availability_zones),
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=subnet_configuration,
            nat_gateways=None
        )

        # add AWS Nat Gateways if Nat Gateway is demanded, and there is internet connectivity for the VPC
        if self.enable_nat:
            if self.vpc_ha:
                for zone_index in range(len(self.availability_zones)):
                    eip = ec2.CfnEIP(self, f"NatGateway EIP {self.availability_zones[zone_index]}")
                    nat_gateway = ec2.CfnNatGateway(self, f"NatGateway {self.availability_zones[zone_index]}",
                        subnet_id=self.vpc.public_subnets[zone_index].subnet_id,
                        allocation_id=eip.attr_allocation_id,
                        connectivity_type="public"
                    )
                    self.nat_gateway_ids.append(nat_gateway.ref)
            else:
                eip = ec2.CfnEIP(self, f"NatGateway EIP {self.availability_zones[0]}")
                nat_gateway = ec2.CfnNatGateway(self, f"NatGateway {self.availability_zones[0]}",
                    subnet_id=self.vpc.public_subnets[0].subnet_id,
                    allocation_id=eip.attr_allocation_id,
                    connectivity_type="public"
                )
                self.nat_gateway_ids.append(nat_gateway.ref)

    def add_public_subnets(self, subnet_oct3: int, mask: int, scope_id: str) -> list:
        if not self.enable_internet:
            raise ValueError('There has to be an Internet Gateway for adding public subnets')

        isubnets = []
        for index in range(len(self.availability_zones)):
            public_subnet = ec2.PublicSubnet(self, f"{scope_id} {self.availability_zones[index]}",
                cidr_block='.'.join((self.oct_1, self.oct_2, str(subnet_oct3 + index), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=self.availability_zones[index]
            )
            public_subnet.add_default_internet_route(self.vpc.internet_gateway_id, self.vpc.internet_connectivity_established)
            isubnets.append(public_subnet)

        if self.vpc_endpoint:
            self.apply_endpoint(rt_ids=[isubnet.route_table.route_table_id for isubnet in isubnets], scope_id=scope_id)

        return isubnets

    def add_private_subnets(self, subnet_oct3: int, mask: int, scope_id: str) -> list:
        isubnets = []
        for index in range(len(self.availability_zones)):
            private_subnet = ec2.PrivateSubnet(self, f"{scope_id} {self.availability_zones[index]}",
                cidr_block='.'.join((self.oct_1, self.oct_2, str(subnet_oct3 + index), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=self.availability_zones[index]
            )
            isubnets.append(private_subnet)

        if self.enable_nat:
            self.add_nat_route(isubnets=isubnets)
        
        if self.vpc_endpoint:
            self.apply_endpoint(rt_ids=[isubnet.route_table.route_table_id for isubnet in isubnets], scope_id=scope_id)

        return isubnets

    def add_isolated_subnets(self, subnet_oct3: int, mask: int, scope_id: str) -> list:
        isubnets = []
        for index in range(len(self.availability_zones)):
            subnet = ec2.Subnet(self, f"{scope_id} {self.availability_zones[index]}",
                cidr_block='.'.join((self.oct_1, self.oct_2, str(subnet_oct3 + index), "0")) + "/24",
                vpc_id=self.vpc.vpc_id,
                availability_zone=self.availability_zones[index]
            )
            isubnets.append(subnet)
        
        return isubnets

    def apply_endpoint(self, rt_ids: list, scope_id: str) -> None:
        ec2.CfnVPCEndpoint(self, f"{scope_id} VPCEndpoint",
            service_name="com.amazonaws." + self.region + ".s3",
            vpc_id=self.vpc.vpc_id,
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

    def add_nat_route(self, isubnets: list) -> None:
        for i in range(len(self.availability_zones)):
            isubnets[i].add_default_nat_route(self.nat_gateway_ids[i] if self.vpc_ha else self.nat_gateway_ids[0])

    def create_tgw(self, bgp_asn: int=65000, scope_id: str=None) -> None:
        # unique bgp_asn number is needed if you have multiple transit gateway in your organization.
        # and the value should not conflict with the other ASN value (if there is any) that you use
        # in your organization
        self.tgw_scope_id = scope_id
        self.tgw = ec2.CfnTransitGateway(self, scope_id,
            amazon_side_asn=bgp_asn,
            auto_accept_shared_attachments='enable',
            default_route_table_association='disable',
            default_route_table_propagation='disable',
            dns_support='enable',
            vpn_ecmp_support='enable'
        )

    # share your transit gateway in your aws organization
    def share_tgw(self, ou_id: str) -> None:
        ram.CfnResourceShare(self, 'RAM{self.tgw_scope_id}',
            name='dc_one_tgw_id_' + self.tgw_scope_id.lower(),
            principals=[ou_id],
            resource_arns=[f"arn:aws:ec2:{self.region}:{self.account}:transit-gateway/{self.tgw.ref}"]
        )

    def create_tgw_attach(self, vpc_id: str, tgw_id: str, subnet_oct3: int, mask: int, scope_id: str=None) -> list:
        """
        Create Transit Gateway Attachment

        Notes:
            Per AWS best practice, each TGW should have its own set of VPC subnets in a VPC. Hence, The 
            creation of VPC subnets is definied along with the definition of adding TGW attachment.

            Multiple TGW attachments, each with a unique transit gateway id, can be attached to same VPC.

        Args:
            vpc_id (str): the resource id of VPC to attach to the transit gateway designated by tgw_id.
            tgw_id (str): the resource id of transit gateway this transit gateway attachment attachs to.
        """

        # since there is circumstance that TGW attachment is added into an existing VPC, it merits to
        # create a Class which is dedicated to handling TGW related resource definition.
        if self.enable_nat:
            res_isubnets = self.add_private_subnets(subnet_oct3=subnet_oct3, mask=mask, scope_id=scope_id)
        else:
            res_isubnets = self.add_isolated_subnets(subnet_oct3=subnet_oct3, mask=mask, scope_id=scope_id)

        self.tgw_attach = ec2.CfnTransitGatewayAttachment(self, scope_id,
            subnet_ids=[isubnet.subnet_id for isubnet in res_isubnets],
            transit_gateway_id=tgw_id,
            vpc_id=vpc_id
        )
        return res_isubnets

    def tgw_route_table(self, tgw_id: str, asso_tgw_attach_id: str, dest_tgw_attach_id: str, dest_cidr: str) -> None:
        """
        Implement Flat Transit Gateway route domains

        """

        # to implement isolated Transit Gateway route domains, coding logic needs to be improved.
        self.tgw_rt = ec2.CfnTransitGatewayRouteTable(self, "{self.tgw_scope_id}Rt",
            transit_gateway_id=tgw_id
        )

        self.tgw_rt_asso = ec2.CfnTransitGatewayRouteTableAssociation(self, "{self.tgw_scope_id}RtAssociation",
            transit_gateway_attachment_id=asso_tgw_attach_id,
            transit_gateway_route_table_id=self.tgw_rt.ref
        )

        self.tgw_route = ec2.CfnTransitGatewayRoute(self, "{self.tgw_scope_id}TGWRoute",
            transit_gateway_route_table_id=self.tgw_rt.ref,
            destination_cidr_block=dest_cidr,
            transit_gateway_attachment_id=dest_tgw_attach_id,

        )

    def add_tgw_route(self, route_tables: list, tgw_id: str, tgw_attach: str, dest_cidr: str, scope_id: str=None) -> None:
        for i in range(len(route_tables)):
            res_tgw_route=ec2.CfnRoute(self, f"{scope_id}{i}",
                            route_table_id=route_tables[i],
                            transit_gateway_id=tgw_id,
                            destination_cidr_block=dest_cidr
            )
            res_tgw_route.add_depends_on(tgw_attach)

    # create vpc in dreamchaser way easily
    def easy_vpc(self) -> None:
        self.add_vpc(vpc_cidr=self.node.try_get_context('DC_VPC_CIDR'), enable_internet=True, enable_nat=True, vpc_ha=self.node.try_get_context('DC_VPC_HA'), vpc_endpoint=True)
        res_pub_isubnets = self.add_public_subnets(subnet_oct3=16, mask=24, scope_id='DCPublicSubnets')
        res_pri_isubnets = self.add_private_subnets(subnet_oct3=128, mask=24, scope_id='DCPrivateSubnets')
        res_iso_isubnets = self.add_isolated_subnets(subnet_oct3=192, mask=24, scope_id='DCIsolatedSubnets')
        self.create_tgw(scope_id="TGW")
        res_tgw_isubnets = self.create_tgw_attach(vpc_id=self.vpc.vpc_id, tgw_id=self.tgw.ref, subnet_oct3=240, mask=24, scope_id="TGWAttach")
        self.add_tgw_route(
            route_tables=[isubnet.route_table.route_table_id for isubnet in res_pri_isubnets], 
            tgw_id=self.tgw.ref, tgw_attach=self.tgw_attach, dest_cidr=self.node.try_get_context('DC_DEST_CIDR'), scope_id='tgwpriroute')
        self.add_tgw_route(route_tables=[isubnet.route_table.route_table_id for isubnet in res_iso_isubnets], 
            tgw_id=self.tgw.ref, tgw_attach=self.tgw_attach, dest_cidr=self.node.try_get_context('DC_DEST_CIDR'), scope_id='tgwisoroute')
        self.add_tgw_route(
            route_tables=[isubnet.route_table.route_table_id for isubnet in res_tgw_isubnets], 
            tgw_id=self.tgw.ref, tgw_attach=self.tgw_attach, dest_cidr=self.node.try_get_context('DC_DEST_CIDR'), scope_id='tgwroute')
        
    # Tags.of(self.vpc).add("DREAMCHASER", "DREAMCHASERVPC")