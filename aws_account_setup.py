from dreamchaser.aws_init import AWSOrg, AWSRam, AWSSsm


# create aws organization with featureset 'ALL' enabled
org_client = AWSOrg('ap-southeast-2')
org_client.create_org()
ou_id = org_client.get_ou_arn()

# enable resource sharing with AWS organizations
ram_client = AWSRam('ap-southeast-2')
ram_client.enable_resource_sharing()

# save 'dreamchaser' org_id in parameter store
ssm_client = AWSSsm('ap-southeast-2')
ssm_client.put_str_para(name='DC_ONE_OU_ID', value=ou_id)