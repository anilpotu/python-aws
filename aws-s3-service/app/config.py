from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None

    s3_bucket_name: str
    sns_topic_arn: str
    sqs_queue_url: str

    # PostgreSQL connection string, e.g.:
    # postgresql://user:password@host:5432/dbname
    database_url: str

    model_config = {"env_file": ".env"}


settings = Settings()
