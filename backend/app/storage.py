import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def get_s3_client():
    if not (settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY):
        return None
    try:
        import boto3
        return boto3.client(
            's3',
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=getattr(settings, 'AWS_REGION', 'ap-south-1')
        )
    except Exception as e:
        logger.warning(f"Failed to initialize S3 client: {e}")
        return None

def upload_file_to_s3(local_path: str, s3_key: str = None, content_type: str = "video/mp4") -> str:
    """
    Upload rendered video, audio, or thumbnail to Amazon S3 (Blueprint Section 5 & 22).
    Returns presigned access URL for the dashboard player.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file does not exist: {local_path}")

    s3 = get_s3_client()
    bucket = getattr(settings, 'S3_BUCKET', 'faceless-studio-media-raj')

    if not s3 or settings.STORAGE_BACKEND != "s3":
        # Fallback to local file URL
        return f"/media/{os.path.basename(os.path.dirname(local_path))}/{os.path.basename(local_path)}"

    s3_key = s3_key or f"videos/{os.path.basename(local_path)}"

    logger.info(f"Uploading {local_path} to s3://{bucket}/{s3_key}...")
    s3.upload_file(
        local_path,
        bucket,
        s3_key,
        ExtraArgs={"ContentType": content_type}
    )

    # Generate a signed URL for secure playback in the dashboard (Blueprint Section 5)
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': s3_key},
        ExpiresIn=86400  # 24-hour validity
    )
    logger.info(f"Generated S3 presigned URL for {s3_key}")
    return url

upload_media = upload_file_to_s3
