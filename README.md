# Jenkins OSS Auto Upload Utils

自动化部署工具，用于将网站静态资源自动上传到对象存储服务（OSS），支持多云平台S3兼容存储。

## 功能特性

- 🚀 **全自动化流程**: Jenkins Pipeline自动触发，无需人工干预
- ☁️ **多云平台支持**: 支持 AWS S3、阿里云OSS、腾讯云COS等S3兼容存储
- 📦 **自动解压**: 自动解压zip压缩包并上传所有文件
- 📧 **邮件通知**: 部署完成后自动发送详细的部署报告邮件
- 📊 **详细日志**: 完整的上传日志和统计信息
- 🔒 **安全可靠**: 支持Jenkins凭证管理，密码参数加密

## 目录结构

```
jenkins-utils/
├── Jenkinsfile              # Jenkins Pipeline配置文件
├── upload_to_oss.py         # Python上传脚本
├── requirements.txt         # Python依赖
├── .gitignore              # Git忽略文件配置
└── README.md               # 项目文档
```

## 快速开始

### 前置要求

1. **Jenkins环境**:
   - Jenkins 2.x 或更高版本
   - 已安装Pipeline插件
   - 已配置Python 3.6+环境

2. **云存储账号**:
   - AWS S3 / 阿里云OSS / 腾讯云COS账号
   - Access Key ID 和 Secret Access Key

3. **邮件服务**:
   - SMTP服务器地址和端口
   - SMTP账号和密码

### 安装步骤

1. **克隆仓库**:
   ```bash
   git clone https://github.com/kukukikits/jenkins-utils.git
   cd jenkins-utils
   ```

2. **安装Python依赖**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **在Jenkins中创建Pipeline任务**:
   - 新建Pipeline类型的任务
   - 在Pipeline配置中选择"Pipeline script from SCM"
   - 配置Git仓库地址
   - 指定Jenkinsfile路径

### 配置说明

#### Pipeline参数

| 参数名称 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| ZIP_FILE_PATH | String | ✓ | 静态资源zip文件的完整路径 |
| S3_BUCKET | String | ✓ | S3存储桶名称 |
| S3_PREFIX | String |  | S3路径前缀（文件夹路径） |
| CLOUD_PROVIDER | Choice | ✓ | 云服务提供商（aws/aliyun/tencent） |
| S3_ENDPOINT | String | * | S3端点URL（阿里云和腾讯云必填） |
| S3_REGION | String | ✓ | S3区域（默认：us-east-1） |
| EMAIL_RECIPIENTS | String | ✓ | 邮件接收人（多个用逗号分隔） |
| SMTP_SERVER | String | ✓ | SMTP服务器地址 |
| SMTP_PORT | String | ✓ | SMTP端口（默认：587） |
| SMTP_USERNAME | String | ✓ | SMTP用户名 |
| SMTP_PASSWORD | Password | ✓ | SMTP密码 |
| AWS_ACCESS_KEY_ID | Password | ✓ | 访问密钥ID |
| AWS_SECRET_ACCESS_KEY | Password | ✓ | 访问密钥 |

\* S3_ENDPOINT 对于非AWS云服务商是必填的

#### 云服务商端点配置示例

**阿里云OSS**:
```
Endpoint: https://oss-cn-hangzhou.aliyuncs.com
Region: cn-hangzhou
```

**腾讯云COS**:
```
Endpoint: https://cos.ap-guangzhou.myqcloud.com
Region: ap-guangzhou
```

**AWS S3**:
```
Endpoint: (留空)
Region: us-east-1
```

### 使用方法

#### 方式1: 在Jenkins UI中触发

1. 打开Jenkins Pipeline任务
2. 点击"Build with Parameters"
3. 填写所有必要参数
4. 点击"Build"开始构建

#### 方式2: 命令行直接执行Python脚本

```bash
python3 upload_to_oss.py \
  --source-dir ./website-dist \
  --bucket my-bucket \
  --prefix static/v1.0 \
  --provider aliyun \
  --endpoint https://oss-cn-hangzhou.aliyuncs.com \
  --region cn-hangzhou \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --email-recipients admin@example.com,dev@example.com \
  --smtp-server smtp.gmail.com \
  --smtp-port 587 \
  --smtp-username your-email@gmail.com \
  --smtp-password your-password
```

## 工作流程

```
┌─────────────────┐
│  触发Pipeline    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  验证参数       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  安装Python依赖  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  解压ZIP文件    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  上传到OSS      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  发送邮件通知   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  清理临时文件   │
└─────────────────┘
```

## 邮件报告示例

部署完成后，会收到包含以下信息的HTML格式邮件：

- ✅ 部署状态
- 📅 部署时间
- ☁️ 云服务提供商
- 📍 目标存储位置
- 📊 上传统计：
  - 总文件数
  - 成功上传文件数
  - 失败文件数
  - 总大小
  - 成功率
- ⚠️ 失败文件详情（如有）

## 故障排查

### 常见问题

1. **认证失败**
   - 检查Access Key和Secret Key是否正确
   - 确认密钥具有上传权限

2. **连接超时**
   - 检查网络连接
   - 验证端点URL是否正确
   - 确认防火墙规则

3. **邮件发送失败**
   - 检查SMTP服务器配置
   - 验证SMTP用户名和密码
   - 确认SMTP端口是否正确（通常587或465）

4. **文件上传失败**
   - 检查存储桶是否存在
   - 确认有足够的存储空间
   - 验证文件路径权限

### 查看日志

Jenkins Pipeline日志:
```
Jenkins任务 > 构建历史 > Console Output
```

Python脚本日志:
```
工作空间中的 oss_upload.log 文件
```

## 安全建议

1. **使用Jenkins凭证管理**:
   - 将敏感信息（Access Key、SMTP密码等）存储在Jenkins凭证中
   - 修改Jenkinsfile使用`credentials()`函数

2. **限制访问权限**:
   - 为OSS创建专用的IAM用户，仅授予必要权限
   - 定期轮换Access Key

3. **启用HTTPS**:
   - 始终使用HTTPS端点
   - 启用SMTP TLS/SSL

## 支持的云平台

| 云平台 | Provider值 | Endpoint示例 |
|-------|-----------|-------------|
| AWS S3 | aws | (留空，使用默认) |
| 阿里云OSS | aliyun | https://oss-cn-beijing.aliyuncs.com |
| 腾讯云COS | tencent | https://cos.ap-guangzhou.myqcloud.com |
| MinIO | aws | http://minio.example.com:9000 |
| 其他S3兼容 | aws | 自定义端点 |

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

- Issue: https://github.com/kukukikits/jenkins-utils/issues
- Author: kukukikits
