=======
JENKINS
=======

A Dreamchaser's project, produced by Jianhua Wu

The `cdk.json` file tells the CDK Toolkit how to execute your app.

The JENKINS package works on Python versions:

* 3.6.x and greater
* 3.7.x and greater
* 3.8.x and greater
* 3.9.x and greater

-------------
Pre-requisite
-------------

* boto3
* access key & secret key of an AWS IAM user with Admin permission
* general AWS knowledge
* Azure Creds
* general Azure knowledge

---------------------------------
Set up Pipenv:
---------------------------------

Install the desired Python version via pyenv::
    pyenv install 3.9.7

Set the local application-specific Python version::
    pyenv local 3.9.7

Set up and activate pipenv::
    pipenv shell

Once the pipenv is activated, you can install the required dependencies::
    pipenv install -e .

At this point you can now synthesize the CloudFormation template for this code.
$ cdk synth


To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -e .`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

