from sqlite3 import _Parameters
import boto3
from urllib3.exceptions import SecurityWarning

# Initialize boto3 clients
ec2 = boto3.client('ec2')
rds = boto3.client('rds')
ssm = boto3.client('ssm')

def create_security_group(vpc_id, group_name, description, allow_ssh=True, allow_http=False):
    #Create a security group for EC2 instance or RDS
    security_group = ec2.create_security_group(
        GroupName=group_name,
        Description=description,
        VpcId=vpc_id
    )
    security_group_id = security_group['GroupId']

    # Allow HTTP and/or SSH access if specified
    if allow_http:
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
    if allow_ssh:
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )
    return security_group_id

def launch_ec2_instance(security_group_id):
        # Launch an EC2 instance
        instance = ec2.run_instances(
            ImageID='ami-0c55b159cbfafe1f0', # Amazon Linux 2 AMI ID
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[security_group_id],
            KeyName='YOUr-KEY-PAIR', # REPLACE WITH YOUR KEY PAIR NAME #
        )
        instance_id = instance['Instances'][0]['InstanceId']

        # Wait for instance to be running
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])

        return instance_id

        def install_apache(instance_id):
            # Send a command to install and start Apache
             response = ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS=RunShellScript",
                Parameters={
                    'commands': [
                        'sudo yum update -y'
                        'sudo amazon-linux-extras install -y apche2',
                        'sudo systemctl start httpd',
                        'sudo systemctl enable httpd'
                    ]
                }
            )

def create_rds_instance(db_security_group_id, db_subnet_group_name):
            # Create an RDS instance
            rds_instance = rds.create_db_instance(
                DBName='YOUR_DATABASE_NAME', # INSERT DATABSE NAME
                DBInstanceIdentifier='you-rds-instance',
                Engine='mysql',
                DBInstanceClass='db.t2.micro',
                MasterUsername='your_master_username',
                MasterUserPassword='your-master-password',
                VpcSecurityGroupIds=[db_security_group_id],
                DBSubnetGroupName=db_subnet_group_name,
                PubliclyAccessible=False,
                StorageType='gp2',
                AllocatedStorage=10, # 20 GB storage, within Free Tier limits
                BackupRetentionPeriod=0, # No backups, within Free Tier limits
                MultiAZ=False, # Single AZ, within Free Tier limits
                AutoMinorVersionUpgrade=False # Diable auto-upgrades, within Free Tier limits 
                )
            
            return rds_instance['DBInstance']['DBInstanceIdentifier']
import boto3

# Initialize boto3 clients
ec2 = boto3.client('ec2')
rds = boto3.client('rds')
ssm = boto3.client('ssm')

def create_security_group(vpc_id, group_name, description, allow_ssh=True, allow_http=False):
    # Create a security group for the EC2 instance or RDS
    security_group = ec2.create_security_group(
        GroupName=group_name,
        Description=description,
        VpcId=vpc_id
    )
    security_group_id = security_group['GroupId']

    # Allow HTTP and/or SSH access if specified
    if allow_http:
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
            ]
        )
    if allow_ssh:
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
            ]
        )

    return security_group_id

def launch_ec2_instance(security_group_id):
    # Launch an EC2 instance
    instance = ec2.run_instances(
        ImageId='ami-0c55b159cbfafe1f0',  # Amazon Linux 2 AMI ID
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=[security_group_id],
        KeyName='your-key-pair',  # Replace with your key pair name
    )
    instance_id = instance['Instances'][0]['InstanceId']

    # Wait for the instance to be running
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])

    return instance_id

def install_apache(instance_id):
    # Send a command to install and start Apache
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={
            'commands': [
                'sudo yum update -y',
                'sudo amazon-linux-extras install -y apache2',
                'sudo systemctl start httpd',
                'sudo systemctl enable httpd'
            ]
        }
    )

def create_rds_instance(db_security_group_id, db_subnet_group_name):
    # Create an RDS instance
    rds_instance = rds.create_db_instance(
        DBName='your_database_name',
        DBInstanceIdentifier='your-rds-instance',
        Engine='mysql',
        DBInstanceClass='db.t2.micro',
        MasterUsername='your_master_username',
        MasterUserPassword='your_master_password',
        VpcSecurityGroupIds=[db_security_group_id],
        DBSubnetGroupName=db_subnet_group_name,
        PubliclyAccessible=False,
        StorageType='gp2',
       AllocatedStorage=20,  # 20 GB storage, within Free Tier limits
       BackupRetentionPeriod=0,  # No backups, within Free Tier limits
       MultiAZ=False,  # Single AZ, within Free Tier limits
       AutoMinorVersionUpgrade=False  # Disable auto-upgrades, within Free Tier limits
    )

    return rds_instance['DBInstance']['DBInstanceIdentifier']

def main():
    # Get the default VPC ID
    vpcs = ec2.describe_vpcs(
        Filters=[{'Name': 'isDefault', 'Values': ['true']}]
    )
    vpc_id = vpcs['Vpcs'][0]['VpcId']

    # Create a security group for the EC2 instance
    ec2_security_group_id = create_security_group(vpc_id, 'frontend-sg', 'Security group for frontend EC2 instance', allow_ssh=True, allow_http=True)

    # Launch an EC2 instance
    ec2_instance_id = launch_ec2_instance(ec2_security_group_id)

    # Install Apache on the EC2 instance
    install_apache(ec2_instance_id)

    # Create a security group for the RDS instance
    db_security_group_id = create_security_group(vpc_id, 'rds-sg', 'Security group for RDS instance', allow_ssh=False, allow_http=False)
    
    # Allow access to the RDS instance from your IP
    your_ip = 'your_ip_address'  # Replace with your IP address
    ec2.authorize_security_group_ingress(
        GroupId=db_security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 3306,
                'ToPort': 3306,
                'IpRanges': [{'CidrIp': f'{your_ip}/32'}]
            },
        ]
    )

    # Create a DB subnet group (replace with your subnet IDs)
    db_subnet_group_name = 'your-db-subnet-group'
    rds.create_db_subnet_group(
        DBSubnetGroupName=db_subnet_group_name,
        DBSubnetGroupDescription='Subnet group for RDS instance',
        SubnetIds=['subnet-0123456789abcdef0', 'subnet-0123456789abcdef1']  # Replace with your subnet IDs
    )

    # Create an RDS instance
    rds_instance_id = create_rds_instance(db_security_group_id, db_subnet_group_name)

    print(f"EC2 instance {ec2_instance_id} launched and Apache installed.")
    print(f"RDS instance {rds_instance_id} created.")

if __name__ == "__main__":
    main()
