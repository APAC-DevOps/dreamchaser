"""""""""""
Provision AWS Resources with CDK on Any AWS Account at any AWS General Region
"""""""""""

...........

...........

.. contents:: Overview

A **Dreamchaser**'s project, produced by Jianhua Wu

The `cdk.json` file tells the CDK Toolkit how to execute your app.

The project works on Python versions:

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

-------------
Configure AWS
-------------

Quick AWS Configuration::
    aws configure

--------------
Set up Pipenv:
--------------

Install the desired Python version via pyenv::
    # pyenv install 3.9.7

Set the local application-specific Python version::
    # pyenv local 3.9.7

Set up and activate pipenv::
    # pipenv shell

Once the pipenv is activated, you can install the required dependencies::
    # pipenv install .


---------------------------
Initialize AWS Organization
---------------------------
From within your python pipenv::
    python3 aws_account_setup.py

-------------------
Enjoy AWS CDK!
-------------------
    |cdk bootstrap
    |cdk list
    |cdk deploy

