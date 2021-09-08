# AWS Cloud Automation
Provision AWS Resources with CDK V2 on Any AWS Account at any AWS General Region
A **Dreamchaser**'s project, produced by **Jianhua Wu**

As of now (September 8th, 2021), the CDK V2 is still in preview stage, hence, breaking change might be introduced in future release. You can track the release status of CDK V2 at [here]https://github.com/aws/aws-cdk/projects/10

The `cdk.json` file tells the CDK Toolkit how to execute your app. And I specify projecte specific contexts with default values in this file.

The project works on Python versions:
* 3.6.x and greater


## Pre-requisite
| Items         |   Versions    |   Mac/Linux   |   Windows     |   Notes   |
|:--------------|:-------:|:------------:|:-------:|:-----------------------|
| AWS Account   |       NA      |       Y       |       Y       | [Login/Registion](https://console.aws.amazon.com/) |
| Nodejs        |   v14.x.x     |       Y       |       Y       | [Install](https://nodejs.org/en/download/package-manager/) |
| Pyenv         |   >=2.0.6     |       Y       |       Y       | [Project Link](https://github.com/pyenv/pyenv)    |
| pipenv        |   latest      |       Y       |       Y       | [Project Link](https://pipenv.pypa.io/en/latest/) |
| Python3       |   >= 3.6.x    |       Y       |       Y       | **Install via Pyenv** |
| IAM Admin User|       NA      |       NA      |       NA      |  access key & secret key of an AWS IAM user with Admin permission |
| vscode        |   latest      |       Y       |       Y       | [Project Link](https://code.visualstudio.com/docs/setup/setup-overview)   |


## Environment Setup
### Configure AWS
```
aws configure
```
### Set up Python Development Environmet
Install the desired Python version via pyenv
```    
pyenv install 3.9.7
```
Set the local application-specific Python version
```
pyenv local 3.9.7
```
Set up and activate pipenv
```
pipenv shell
```
Once the pipenv is activated, you can install the required dependencies
```
pipenv install .
```


## Initialize AWS Organization
From within your python pipenv, cd into the root directory of this project
```
python3 aws_account_setup.py
```

#Enjoy AWS CDK!
```
    cdk bootstrap
    cdk list
    cdk deploy
```

