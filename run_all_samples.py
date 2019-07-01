import argparse
from key_vault_sample_base import run_all_samples
from authentication_sample import AuthenticationSample
from key_vault_sample_config import KeyVaultSampleConfig


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ci', default=False, action='store_true',
                        help='indicates that only samples which run as part of the ci should be run')
    parser.add_argument('--tenant-id', dest='tenant_id', type=str, default=None,
                        help='the tenant id of the tenant in which to run the sample')
    parser.add_argument('--subscription-id', dest='subscription_id', type=str, default=None,
                        help='the subscription id of the subscription in which to run the sample')
    parser.add_argument('--client-id', dest='client_id', type=str, default=None,
                        help='the client id of the service principal to run the sample')
    parser.add_argument('--client-oid', dest='client_oid', type=str, default=None,
                        help='the object id of the service principal to run the sample')
    parser.add_argument('--client-secret', dest='client_secret', type=str, default=None,
                        help='the authentication secret of the service principal to run the sample')
    parser.add_argument('--samples', nargs='*', type=str,
                        help='names of specific samples to run')
    args = parser.parse_args()

    config = KeyVaultSampleConfig()

    if args.tenant_id:
        config.tenant_id = args.tenant_id
    if args.subscription_id:
        config.subscription_id = args.subscription_id
    if args.client_id:
        config.client_id = args.client_id
    if args.client_oid:
        config.client_oid = args.client_oid
    if args.client_secret:
        config.client_secret = args.client_secret

    run_all_samples([AuthenticationSample(config=config)],
                    requested=args.samples or [])
