#!/usr/bin/env python3
"""
OSS Upload Script for Jenkins Automation

This script uploads static resources to S3-compatible cloud storage (OSS)
and sends email notifications upon completion.

Supports:
- AWS S3
- Alibaba Cloud OSS
- Tencent Cloud COS
- Other S3-compatible storage services
- Download resources from URLs before uploading
"""

import argparse
import os
import sys
import logging
import smtplib
import html
import zipfile
import mimetypes
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("Error: boto3 library is required. Install with: pip install boto3")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests library is required. Install with: pip install requests")
    sys.exit(1)

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger = logging.getLogger(__name__)
    logger.warning("python-magic not available. Falling back to mimetypes for content type detection.")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('oss_upload.log')
    ]
)
logger = logging.getLogger(__name__)


def download_file(url: str, dest_path: Path) -> bool:
    """
    Download a file from URL to local path
    
    Args:
        url: URL to download from
        dest_path: Local path to save the file
        
    Returns:
        True if download successful, False otherwise
    """
    try:
        logger.info(f"Downloading from: {url}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) < 8192:  # Log every MB
                            logger.info(f"Download progress: {progress:.1f}% ({downloaded}/{total_size} bytes)")
        
        logger.info(f"✓ Downloaded successfully: {dest_path} ({downloaded} bytes)")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to download {url}: {e}")
        return False


def extract_zip(zip_path: Path, extract_dir: Path) -> bool:
    """
    Extract a zip file to a directory
    
    Args:
        zip_path: Path to the zip file
        extract_dir: Directory to extract to
        
    Returns:
        True if extraction successful, False otherwise
    """
    try:
        logger.info(f"Extracting: {zip_path} -> {extract_dir}")
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        file_count = len(list(extract_dir.rglob('*')))
        logger.info(f"✓ Extracted {file_count} items successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to extract {zip_path}: {e}")
        return False


def download_and_extract_resources(urls: List[str], download_dir: Path, extract_dir: Path) -> bool:
    """
    Download zip files from URLs and extract them
    
    Args:
        urls: List of URLs to download
        download_dir: Directory to download files to
        extract_dir: Directory to extract files to
        
    Returns:
        True if all downloads and extractions successful, False otherwise
    """
    download_dir.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    all_success = True
    
    for idx, url in enumerate(urls, 1):
        logger.info(f"\n[{idx}/{len(urls)}] Processing URL: {url}")
        
        # Determine filename from URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = f"download_{idx}.zip"
        
        if not filename.endswith('.zip'):
            filename += '.zip'
        
        download_path = download_dir / filename
        
        # Download the file
        if not download_file(url, download_path):
            all_success = False
            continue
        
        # Extract the file
        if not extract_zip(download_path, extract_dir):
            all_success = False
            continue
    
    return all_success


class OSSUploader:
    """Handle uploads to S3-compatible cloud storage"""
    
    def __init__(self, provider: str, bucket: str, prefix: str, endpoint: str,
                 region: str, access_key: str, secret_key: str):
        """
        Initialize OSS uploader
        
        Args:
            provider: Cloud provider (aws, aliyun, tencent)
            bucket: S3 bucket name
            prefix: S3 prefix/folder path
            endpoint: S3 endpoint URL
            region: S3 region
            access_key: Access key ID
            secret_key: Secret access key
        """
        self.provider = provider
        self.bucket = bucket
        self.prefix = prefix.strip('/') if prefix else ''
        self.region = region
        self.uploaded_files: List[str] = []
        self.failed_files: List[Dict[str, str]] = []
        
        # Configure S3 client based on provider
        config_kwargs = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'region_name': region
        }
        
        # Allow custom endpoint for any provider (including AWS for MinIO, etc.)
        if endpoint:
            config_kwargs['endpoint_url'] = endpoint
            logger.info(f"Using custom endpoint: {endpoint}")
        
        try:
            self.s3_client = boto3.client('s3', **config_kwargs)
            logger.info(f"S3 client initialized for provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def upload_directory(self, source_dir: str) -> Dict[str, Any]:
        """
        Upload all files from a directory to S3
        
        Args:
            source_dir: Local directory path to upload
            
        Returns:
            Dictionary with upload statistics
        """
        source_path = Path(source_dir)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        if not source_path.is_dir():
            raise ValueError(f"Source path is not a directory: {source_dir}")
        
        logger.info(f"Starting upload from: {source_dir}")
        logger.info(f"Target bucket: {self.bucket}")
        logger.info(f"Target prefix: {self.prefix or '(root)'}")
        
        # Get all files recursively
        files_to_upload = [f for f in source_path.rglob('*') if f.is_file()]
        total_files = len(files_to_upload)
        total_size = sum(f.stat().st_size for f in files_to_upload)
        
        logger.info(f"Found {total_files} files to upload (total size: {self._format_size(total_size)})")
        
        # Upload each file
        for idx, file_path in enumerate(files_to_upload, 1):
            relative_path = file_path.relative_to(source_path)
            s3_key = str(Path(self.prefix) / relative_path) if self.prefix else str(relative_path)
            # Normalize path separators for S3 (use forward slashes)
            s3_key = s3_key.replace('\\', '/')
            
            try:
                logger.info(f"[{idx}/{total_files}] Uploading: {relative_path} -> s3://{self.bucket}/{s3_key}")
                
                # Determine content type based on file extension
                content_type = self._get_content_type(file_path)
                
                extra_args = {}
                if content_type:
                    extra_args['ContentType'] = content_type
                
                self.s3_client.upload_file(
                    str(file_path),
                    self.bucket,
                    s3_key,
                    ExtraArgs=extra_args
                )
                
                self.uploaded_files.append(s3_key)
                logger.info(f"✓ Successfully uploaded: {s3_key}")
                
            except ClientError as e:
                error_msg = str(e)
                logger.error(f"✗ Failed to upload {relative_path}: {error_msg}")
                self.failed_files.append({
                    'file': str(relative_path),
                    'error': error_msg
                })
            except Exception as e:
                error_msg = str(e)
                logger.error(f"✗ Unexpected error uploading {relative_path}: {error_msg}")
                self.failed_files.append({
                    'file': str(relative_path),
                    'error': error_msg
                })
        
        # Generate upload summary
        summary = {
            'total_files': total_files,
            'total_size': total_size,
            'uploaded_count': len(self.uploaded_files),
            'failed_count': len(self.failed_files),
            'uploaded_files': self.uploaded_files,
            'failed_files': self.failed_files,
            'success_rate': (len(self.uploaded_files) / total_files * 100) if total_files > 0 else 0
        }
        
        logger.info(f"\n{'='*60}")
        logger.info("Upload Summary:")
        logger.info(f"Total files: {summary['total_files']}")
        logger.info(f"Uploaded: {summary['uploaded_count']}")
        logger.info(f"Failed: {summary['failed_count']}")
        logger.info(f"Success rate: {summary['success_rate']:.2f}%")
        logger.info(f"{'='*60}\n")
        
        return summary
    
    @staticmethod
    def _get_content_type(file_path: Path) -> str:
        """
        Determine content type using python-magic (if available) or mimetypes
        
        This provides robust content type detection for production use.
        Falls back to mimetypes library if python-magic is not available.
        """
        content_type = ''
        
        # Try python-magic first (most accurate)
        if HAS_MAGIC:
            try:
                mime = magic.Magic(mime=True)
                content_type = mime.from_file(str(file_path))
                if content_type:
                    return content_type
            except Exception as e:
                logger.debug(f"python-magic failed for {file_path}: {e}")
        
        # Fall back to mimetypes (reliable, less accurate)
        content_type, _ = mimetypes.guess_type(str(file_path))
        if content_type:
            return content_type
        
        # Last resort: basic extension mapping for common web assets
        extension_map = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.mjs': 'application/javascript',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.otf': 'font/otf',
            '.eot': 'application/vnd.ms-fontobject',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.zip': 'application/zip',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip',
        }
        return extension_map.get(file_path.suffix.lower(), 'application/octet-stream')
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


class EmailNotifier:
    """Handle email notifications"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """
        Initialize email notifier
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_deployment_report(self, recipients: List[str], upload_summary: Dict[str, Any],
                               bucket: str, prefix: str, provider: str) -> bool:
        """
        Send deployment completion email
        
        Args:
            recipients: List of email recipients
            upload_summary: Upload statistics dictionary
            bucket: S3 bucket name
            prefix: S3 prefix
            provider: Cloud provider name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"✓ OSS Deployment Completed - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Create email body
            target_path = f"{bucket}/{prefix}" if prefix else bucket
            
            # Plain text version
            text_body = f"""
OSS Deployment Report
{'='*60}

Deployment completed successfully!

Cloud Provider: {provider.upper()}
Target Location: s3://{target_path}
Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Upload Statistics:
- Total Files: {upload_summary['total_files']}
- Successfully Uploaded: {upload_summary['uploaded_count']}
- Failed: {upload_summary['failed_count']}
- Total Size: {OSSUploader._format_size(upload_summary['total_size'])}
- Success Rate: {upload_summary['success_rate']:.2f}%

"""
            
            if upload_summary['failed_files']:
                text_body += "\nFailed Files:\n"
                for failed in upload_summary['failed_files']:
                    text_body += f"- {failed['file']}: {failed['error']}\n"
            
            text_body += f"\n{'='*60}\n"
            text_body += "This is an automated notification from Jenkins OSS Upload Pipeline.\n"
            
            # HTML version
            html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
        .stats {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
        .stat-row {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; }}
        .stat-label {{ font-weight: bold; }}
        .failed {{ color: #f44336; }}
        .success {{ color: #4CAF50; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ OSS Deployment Completed</h1>
            <p>Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <h2>Deployment Details</h2>
            <div class="stats">
                <div class="stat-row">
                    <span class="stat-label">Cloud Provider:</span>
                    <span>{provider.upper()}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Target Location:</span>
                    <span>s3://{target_path}</span>
                </div>
            </div>
            
            <h2>Upload Statistics</h2>
            <div class="stats">
                <div class="stat-row">
                    <span class="stat-label">Total Files:</span>
                    <span>{upload_summary['total_files']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Successfully Uploaded:</span>
                    <span class="success">{upload_summary['uploaded_count']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Failed:</span>
                    <span class="{'failed' if upload_summary['failed_count'] > 0 else 'success'}">{upload_summary['failed_count']}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total Size:</span>
                    <span>{OSSUploader._format_size(upload_summary['total_size'])}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Success Rate:</span>
                    <span class="{'success' if upload_summary['success_rate'] == 100 else 'failed'}">{upload_summary['success_rate']:.2f}%</span>
                </div>
            </div>
"""
            
            if upload_summary['failed_files']:
                html_body += """
            <h2>Failed Files</h2>
            <div class="stats">
                <ul>
"""
                for failed in upload_summary['failed_files']:
                    escaped_file = html.escape(failed['file'])
                    escaped_error = html.escape(failed['error'])
                    html_body += f"<li class='failed'>{escaped_file}: {escaped_error}</li>\n"
                html_body += """
                </ul>
            </div>
"""
            
            html_body += """
        </div>
        
        <div class="footer">
            <p>This is an automated notification from Jenkins OSS Upload Pipeline.</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Attach both versions
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Send email
            logger.info(f"Sending deployment report to: {', '.join(recipients)}")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info("✓ Deployment report email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to send email notification: {e}")
            return False


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Upload static resources to S3-compatible OSS and send email notification'
    )
    
    # Resource source parameters - support both URLs and local directory
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--source-dir', help='Source directory to upload (local files)')
    source_group.add_argument('--download-urls', help='Comma-separated URLs to download and extract before uploading')
    
    # Upload parameters
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--prefix', default='', help='S3 prefix/folder path')
    parser.add_argument('--provider', required=True, choices=['aws', 'aliyun', 'tencent'],
                       help='Cloud provider type')
    parser.add_argument('--endpoint', default='', help='S3 endpoint URL (required for non-AWS)')
    parser.add_argument('--region', default='us-east-1', help='S3 region')
    parser.add_argument('--access-key', required=True, help='Access Key ID')
    parser.add_argument('--secret-key', required=True, help='Secret Access Key')
    
    # Email parameters
    parser.add_argument('--email-recipients', required=True,
                       help='Comma-separated email addresses for notifications')
    parser.add_argument('--smtp-server', required=True, help='SMTP server address')
    parser.add_argument('--smtp-port', type=int, default=587, help='SMTP server port')
    parser.add_argument('--smtp-username', required=True, help='SMTP username')
    parser.add_argument('--smtp-password', required=True, help='SMTP password')
    
    # Working directory parameters
    parser.add_argument('--download-dir', default='downloads', help='Directory for downloaded files')
    parser.add_argument('--extract-dir', default='extracted_files', help='Directory for extracted files')
    
    args = parser.parse_args()
    
    try:
        # Determine source directory
        source_dir = args.source_dir
        
        # If URLs are provided, download and extract them first
        if args.download_urls:
            logger.info("=" * 60)
            logger.info("DOWNLOADING AND EXTRACTING RESOURCES")
            logger.info("=" * 60)
            
            urls = [url.strip() for url in args.download_urls.split(',') if url.strip()]
            if not urls:
                logger.error("No valid URLs provided")
                sys.exit(1)
            
            logger.info(f"Processing {len(urls)} URL(s)")
            
            download_dir = Path(args.download_dir)
            extract_dir = Path(args.extract_dir)
            
            if not download_and_extract_resources(urls, download_dir, extract_dir):
                logger.error("Failed to download and extract all resources")
                sys.exit(1)
            
            source_dir = str(extract_dir)
            logger.info(f"✓ All resources downloaded and extracted to: {source_dir}")
        
        # Initialize uploader
        logger.info("\n" + "=" * 60)
        logger.info("UPLOADING TO OSS")
        logger.info("=" * 60)
        
        uploader = OSSUploader(
            provider=args.provider,
            bucket=args.bucket,
            prefix=args.prefix,
            endpoint=args.endpoint,
            region=args.region,
            access_key=args.access_key,
            secret_key=args.secret_key
        )
        
        # Upload files
        upload_summary = uploader.upload_directory(args.source_dir)
        
        # Initialize email notifier
        notifier = EmailNotifier(
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            username=args.smtp_username,
            password=args.smtp_password
        )
        
        # Send notification
        recipients = [email.strip() for email in args.email_recipients.split(',')]
        notifier.send_deployment_report(
            recipients=recipients,
            upload_summary=upload_summary,
            bucket=args.bucket,
            prefix=args.prefix,
            provider=args.provider
        )
        
        # Exit with appropriate status
        if upload_summary['failed_count'] > 0:
            logger.warning(f"Completed with {upload_summary['failed_count']} failures")
            sys.exit(1)
        else:
            logger.info("All operations completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
