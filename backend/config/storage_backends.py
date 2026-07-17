from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseMediaStorage(S3Boto3Storage):
    location = 'documents'
    file_overwrite = False
    default_acl = None
    querystring_auth = False