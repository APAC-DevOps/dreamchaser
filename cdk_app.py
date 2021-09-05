#!/usr/bin/env python3
import os
from constructs import Construct
from aws_cdk import App, Stack, Environment
from aws_cdk import aws_s3 as s3
from vpc.vpc_core import VPCStack

#cdk bootstrap yourAWSAccountId/desiredAWSRegion --profile dreamchaser-one
#cdk deploy -c DREAMCHASER_CDK_ACCOUNT=yourAWSAccountId -c DREAMCHASER_CDK_REGION=desiredAWSRegion DREAMCHASER-VPC-STACK-MAIN

app_vpc = App()

if app_vpc.node.try_get_context("DREAMCHASER_CDK_ACCOUNT"):
        dreamchaser_cdk_account = app_vpc.node.try_get_context("DREAMCHASER_CDK_ACCOUNT")
else:
        dreamchaser_cdk_account = os.getenv("CDK_DEFAULT_ACCOUNT")

if app_vpc.node.try_get_context("DREAMCHASER_CDK_REGION"):
        dreamchaser_cdk_region = app_vpc.node.try_get_context("DREAMCHASER_CDK_REGION")
else:
        dreamchaser_cdk_region = os.getenv("CDK_DEFAULT_REGION")

# class MyVPC(Construct):
#     def __init__(self, scope: Construct, id: str, *, prod=False) -> None:
#         super().__init__(scope, id)
#     VPCStack(app_vpc, "DREAMCHASER-VPC-STACK-MAIN",
#                      env=Environment(
#                         account=dreamchaser_cdk_account,
#                         region=dreamchaser_cdk_region
#                      )
#              )

# MyVPC(app_vpc, "alpha")

vpc_stack = VPCStack(app_vpc, "DREAMCHASER-VPC-STACK-MAIN",
                     env=Environment(
                        account=dreamchaser_cdk_account,
                        region=dreamchaser_cdk_region
                     )
            )

app_vpc.synth()