from dreamchaser.aws_init import AWSOrg


# create aws organization with featureset 'ALL' enabled
org_client = AWSOrg('organizations', 'ap-southeast-2')
org_client.create_org()