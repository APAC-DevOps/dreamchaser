import boto3
from botocore.client import ClientError

class AWSOrg():
    def __init__(self, region_name: str, policy_type: str='SERVICE_CONTROL_POLICY',
                org_unit: str='dreamchaser', **kwargs) -> None:
        self.client = boto3.client('organizations', region_name = 'ap-southeast-2')
        self.policy_type = policy_type
        self.org_unit = org_unit
    
    def create_org(self, feature_set: str='ALL'):
        try:
            self.client.create_organization(FeatureSet=feature_set)
        except ClientError as e:
            if e.response['Error']['Code'] != 'AlreadyInOrganizationException':
                print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
                exit(127)
        
        self.enable_policy(policy_type='SERVICE_CONTROL_POLICY')
        self.create_ou()

    def enable_policy(self, root_id: str=None, policy_type: str='SERVICE_CONTROL_POLICY') -> None:
        try:
            if not root_id:
                root_id = self.client.list_roots()['Roots'][0]['Id']

            self.client.enable_policy_type(RootId=root_id, PolicyType=policy_type)
        except ClientError as e:
            if e.response['Error']['Code'] != 'PolicyTypeAlreadyEnabledException':
                print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
                exit(157)

    def create_ou(self, parent_id: str=None, org_unit: str=None) -> None:
        try:
            if not parent_id:
                parent_id = self.client.list_roots()['Roots'][0]['Id']

            self.client.create_organizational_unit(ParentId=parent_id, Name=(org_unit or self.org_unit))
        except ClientError as e:
            if e.response['Error']['Code'] != 'DuplicateOrganizationalUnitException':
                print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
                exit(137)

    def get_ou_arn(self, parent_id: str=None, org_unit: str=None) -> str:
        try:
            if not parent_id:
                    parent_id = self.client.list_roots()['Roots'][0]['Id']
            res_list_ou = self.client.list_organizational_units_for_parent(ParentId=parent_id)
            
            for ou in res_list_ou['OrganizationalUnits']:
                if ou['Name'] == (org_unit or self.org_unit):
                    return ou['Arn']

        except ClientError as e:
            print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
            exit(177)


class AWSRam():
    def __init__(self, region_name: str='ap-southeast-2', **kwargs) -> None:
        self.client = boto3.client('ram', region_name = 'ap-southeast-2')

    def enable_resource_sharing(self):
        self.client.enable_sharing_with_aws_organization()


class AWSSsm():
    def __init__(self, region_name: str='ap-southeast-2', **kwargs) -> None:
        self.client = boto3.client('ssm', region_name = 'ap-southeast-2')

    def get_para(self, name: str):
        try:
            return self.client.get_parameter(Name=name, WithDecryption=False)['Parameter']['Value']
        except ClientError as e:
            print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
            exit(197)

    def put_str_para(self, name: str, value: str):
        try:
            self.client.put_parameter(Name=name, Value=value, Type='String', Overwrite=True)
        except ClientError as e:
            print(e.response['Error']['Message'], "Error Code:", e.response['Error']['Code'])
            exit(197)