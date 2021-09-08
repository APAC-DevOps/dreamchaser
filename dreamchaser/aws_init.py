import boto3
from botocore.client import ClientError

class AWSOrg():
    def __init__(self, service: str, region_name: str, policy_type: str='SERVICE_CONTROL_POLICY', **kwargs) -> None:
        self.client = boto3.client(service, region_name = 'ap-southeast-2')
        self.policy_type = policy_type
    
    def create_org(self, feature_set: str='ALL'):
        try:
            self.client.create_organization(FeatureSet=feature_set)
        except ClientError as e:
            if e.response['Error']['Code'] != 'AlreadyInOrganizationException':
                print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
                exit(127)

        self.create_ou()
        self.enable_policy(policy_type='SERVICE_CONTROL_POLICY')

    def create_ou(self, parent_id: str=None, org_unit: str='dreamchaser'):
        try:
            if not parent_id:
                parent_id = self.root_id = self.client.list_roots()['Roots'][0]['Id']
            self.client.create_organizational_unit(ParentId=parent_id, Name=org_unit)
        except ClientError as e:
            if e.response['Error']['Code'] != 'DuplicateOrganizationalUnitException':
                print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
                exit(137)

    def enable_policy(self, root_id: str=None, policy_type: str='SERVICE_CONTROL_POLICY'):
        try:
            if not root_id:
                root_id = self.root_id = self.client.list_roots()['Roots'][0]['Id']
            self.client.enable_policy_type(RootId=root_id, PolicyType=policy_type)
        except ClientError as e:
            if e.response['Error']['Code'] != 'PolicyTypeAlreadyEnabledException':
                print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
                exit(157)