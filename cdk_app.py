#!/usr/bin/env python3
import os
import time
from constructs import Construct
from aws_cdk import App, Stack, Environment
from aws_cdk import aws_s3 as s3
from vpc.vpc_core import VPCStack
from dreamchaser.aws_init import AWSSsm

#cdk bootstrap yourAWSAccountId/desiredAWSRegion --profile yourAwsProfile
#cdk deploy -c EASY_VPC=True DREAMCHASER-VPC-STACK-MAIN

app_vpc = App()
ssm_client = AWSSsm('ap-southeast-2')
aws_account = app_vpc.node.try_get_context("AWS_ACCOUNT") or os.getenv("CDK_DEFAULT_ACCOUNT")
aws_region = app_vpc.node.try_get_context("AWS_REGION") or os.getenv("CDK_DEFAULT_REGION")

vpc_stack = VPCStack(app_vpc, "DREAMCHASER-VPC-STACK-MAIN",
                     env=Environment(
                        account=aws_account,
                        region=aws_region
                     )
            )

# assume you don't have AWS Organization set up, and there is one AWS account only,
if app_vpc.node.try_get_context("EASY_VPC"):
        vpc_stack.easy_vpc()
else:
        # the purpose of the lines of code below is to show how DreamChaser construct can be used flexibibly
        # you can make changes per your project requirements
        ou_id = app_vpc.node.try_get_context("OU_ID") or ssm_client.get_para(name='DC_ONE_OU_ID')
        vpc_stack.add_vpc(vpc_cidr=app_vpc.node.try_get_context('DC_VPC_CIDR'), enable_internet=True, enable_nat=True, vpc_ha=app_vpc.node.try_get_context('DC_VPC_HA'), vpc_endpoint=True)
        res_pub_isubnets = vpc_stack.add_public_subnets(subnet_oct3=16, mask=24, scope_id='DCPublicSubnets')
        res_pri_isubnets = vpc_stack.add_private_subnets(subnet_oct3=128, mask=24, scope_id='DCPrivateSubnets')
        res_iso_isubnets = vpc_stack.add_isolated_subnets(subnet_oct3=192, mask=24, scope_id='DCIsolatedSubnets')
        vpc_stack.create_tgw(scope_id="TGW")
        time.sleep(5)
        vpc_stack.share_tgw(ou_id=ou_id)
        res_tgw_isubnets = vpc_stack.create_tgw_attach(
                vpc_id=app_vpc.node.try_get_context("VPC_ID") or vpc_stack.vpc.vpc_id,
                tgw_id=app_vpc.node.try_get_context("TGW_ID") or vpc_stack.tgw.ref,
                subnet_oct3=240,
                mask=24,
                scope_id="TGWAttach"
        )
        vpc_stack.tgw_route_table( 
                tgw_id=app_vpc.node.try_get_context("TGW_ID") or vpc_stack.tgw.ref,
                asso_tgw_attach_id=app_vpc.node.try_get_context("ASSO_TGW_ATTACH_ID") or vpc_stack.tgw_attach.ref,
                dest_tgw_attach_id=app_vpc.node.try_get_context("DEST_TGW_ATTACH_ID") or vpc_stack.tgw_attach.ref,
                dest_cidr=app_vpc.node.try_get_context("DC_DEST_CIDR")      # specify your own destination CIDR here.
        )
        vpc_stack.add_tgw_route(route_tables=[isubnet.route_table.route_table_id for isubnet in res_pri_isubnets], 
                tgw_id=vpc_stack.tgw.ref,
                tgw_attach=vpc_stack.tgw_attach,
                dest_cidr=app_vpc.node.try_get_context('DC_DEST_CIDR'),
                scope_id='pritgwroute'
        )
        vpc_stack.add_tgw_route(route_tables=[isubnet.route_table.route_table_id for isubnet in res_iso_isubnets],
                tgw_id=vpc_stack.tgw.ref,
                tgw_attach=vpc_stack.tgw_attach,
                dest_cidr=app_vpc.node.try_get_context('DC_DEST_CIDR'),
                scope_id='isotgwroute'
        )

        vpc_stack.add_tgw_route(
            route_tables=[isubnet.route_table.route_table_id for isubnet in res_tgw_isubnets], 
            tgw_id=vpc_stack.tgw.ref,
            tgw_attach=vpc_stack.tgw_attach,
            dest_cidr=vpc_stack.node.try_get_context('DC_DEST_CIDR'),
            scope_id='tgwroute'
        )

app_vpc.synth()