#!/usr/bin/env python3
import os
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
        vpc_stack.vpc(vpc_cidr=app_vpc.node.try_get_context('DC_VPC_CIDR'), vpc_ha=app_vpc.node.try_get_context('DC_VPC_HA'))
        vpc_stack.apply_endpoint(vpc_id=vpc_stack.vpc.vpc_id, rt_ids=vpc_stack.route_tables)
        vpc_stack.create_tgw()
        vpc_stack.share_tgw(ou_id=ou_id, tgw_id=app_vpc.node.try_get_context("TGW_ID") or vpc_stack.tgw.ref)
        vpc_stack.create_tgw_attach(
                vpc_id=app_vpc.node.try_get_context("VPC_ID") or vpc_stack.vpc.vpc_id,
                tgw_id=app_vpc.node.try_get_context("TGW_ID") or vpc_stack.tgw.ref,
                tgw_subnets=app_vpc.node.try_get_context("TGW_SUBNETS") or vpc_stack.tgw_subnets,
        )
        vpc_stack.create_tgw_route(
                tgw_id=app_vpc.node.try_get_context("TGW_ID") or vpc_stack.tgw.ref,
                asso_tgw_attach_id=app_vpc.node.try_get_context("ASSO_TGW_ATTACH_ID") or vpc_stack.tgw_attach.ref,
                dest_tgw_attach_id=app_vpc.node.try_get_context("DEST_TGW_ATTACH_ID") or vpc_stack.tgw_attach.ref,
                dest_cidr=app_vpc.node.try_get_context("DC_DEST_CIDR")      # specify your own destination CIDR here.
        )

app_vpc.synth()