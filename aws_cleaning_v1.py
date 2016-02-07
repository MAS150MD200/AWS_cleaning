__author__ = 'atsvetkov'


from boto3.session import Session
from datetime import datetime, timedelta, timezone
from pprint import pprint as pp


today = datetime.now(timezone.utc) + timedelta(days=1) # today + 1 because we want all of today
one_year = timedelta(days=365)
two_weeks = timedelta(days=14)
start_date = today - two_weeks
regions = ["us-west-2",
           "ap-southeast-1",
           "us-east-1",
           "ap-northeast-1",
           "eu-west-1",
           "ap-southeast-2",
           "sa-east-1",
           "eu-central-1"]

region = regions[7]
# 194094
# 66126
# 253606
# 58592
# 62393
# 52486
# 51281
# 46789

# use ~/.aws/credentials:
session = Session(profile_name="sre-readonly", region_name=region)


def get_available_volumes():

    ec2 = session.resource("ec2", region_name=region)

    available_volumes = ec2.volumes.filter(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )
    return available_volumes


def get_metrics(volume_id):
    """Get volume idle time on an individual volume over `start_date`
       to today"""

    cloudwatch = session.client("cloudwatch", region_name=region)

    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/EBS',
        MetricName='VolumeIdleTime',
        Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
        Period=3600,  # every hour
        StartTime=start_date,
        EndTime=today,
        Statistics=['Minimum'],
        Unit='Seconds'
    )
    return metrics['Datapoints']


def is_candidate(volume_id):
    """Make sure the volume has not been used in the past two weeks"""
    metrics = get_metrics(volume_id)
    if len(metrics):
        for metric in metrics:
            # idle time is 5 minute interval aggregate so we use
            # 299 seconds to test if we're lower than that
            if metric['Minimum'] < 299:
                return False
    # if the volume had no metrics lower than 299 it's probably not
    # actually being used for anything so we can include it as
    # a candidate for deletion
    return True


def find_snapshots():

    ec2 = session.resource("ec2", region_name=region)
    snapshots = ec2.snapshots.all()

    sn_volume_size = 0
    print(region)
    for sn in snapshots:
        if (today - sn.start_time > one_year) or True:
            sn_volume_size += sn.volume_size
            print(sn.id, sn.volume_size, sn.start_time)
    print("Total size:", sn_volume_size)

def main():

    find_snapshots()

    exit()


    print(region)
    all_vols = get_available_volumes()
    for vol in all_vols:
        # pp(dir(vol))
        # vol_metrics = get_metrics(vol.id)
        # print(is_candidate(vol_metrics))
        print(is_candidate(vol.id), vol.id, vol.size)

        # break


if __name__ == "__main__":
    main()
