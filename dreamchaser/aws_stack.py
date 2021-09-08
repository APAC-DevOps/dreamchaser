import sys
import boto3
import json
from botocore.client import ClientError

class CfnStack():
    def __init__(self, region_name: str, **kwargs) -> None:
        self.client = boto3.client('cloudformation', region_name = 'ap-southeast-2')

    def describe_stack(self, stack_name: str=None):
        cfn_outputs = self.client.describe_stacks(StackName = stack_name)['Stacks'][0]['Outputs']
        output_len = len(cfn_outputs)
        i=0
        output_map = {}
        while i<output_len:
            output_map[cfn_outputs[i]['OutputKey']]  = cfn_outputs[i]['OutputValue']
            i = i + 1
        return output_map

    def update_stack(self, stack_name: str=None, template: str=None, parameters: list=None):
        stack_response = self.client.update_stack(
            StackName = stack_name,
            TemplateURL = template,
            Parameters = parameters,
            Capabilities = [
                'CAPABILITY_NAMED_IAM',
                'CAPABILITY_AUTO_EXPAND'
            ]
        )

    def create_stack(self, stack_name: str=None, template: str=None, parameters: list=None, timeout=30):
        stack_response = self.client.create_stack(
        StackName = stack_name,
        TemplateURL = template,
        Parameters = parameters,
        TimeoutInMinutes=timeout,
        Capabilities=[
            'CAPABILITY_NAMED_IAM',
            'CAPABILITY_AUTO_EXPAND'
        ],
        OnFailure='ROLLBACK',
        EnableTerminationProtection = True
        )

    def write_output(self, stack_name: str=None, output=None):
        cfn_outputs = self.describe_stack(stack_name=stack_name)
        with open(output, 'w+') as foutput:
            json.dump(cfn_outputs, foutput, indent = 4)

    def create_update_stack(self, stack_name: str=None, template=None, parameters=None, output=None, timeout=30):
        try:
            self.describe_stack(stack_name=stack_name)
            try:
                print("Updating stack: " + stack_name)
                self.update_stack(stack_name=stack_name, template=template, parameters=parameters)
                stack_waiter = self.client.get_waiter('stack_update_complete')
                stack_waiter.wait(StackName=stack_name)
                if output:
                    print("Config ouput written to: {}".format(output))
                    self.write_output(stack_name=stack_name, output=output)
                print("Successfully updated stack: " + stack_name)
                return 0
            except ClientError as e:
                error_code = int(e.response['ResponseMetadata']['HTTPStatusCode'])
                if error_code == 400:
                    print("Nothing to be updated on stack: " + stack_name)
                    return 0
                print("Error Occured.")
                sys.exit(error_code)
        except ClientError as e:
            error_code = int(e.response['ResponseMetadata']['HTTPStatusCode'])
            if error_code == 403:
                sys.exit("Private Cloudformation stack. Access denied!")
            elif error_code == 400:
                print("Stack does not exist! Creating stack: " + stack_name)
                self.create_stack(stack_name=stack_name, template=template, parameters=parameters, timeout=timeout)
                stack_waiter = self.client.get_waiter('stack_create_complete')
                stack_waiter.wait(StackName=stack_name)
                if output:
                    print("Config ouput written to: {}".format(output))
                    self.write_output(stack_name=stack_name, output=output)
                print("Created new stack: " + stack_name)
                return 0
