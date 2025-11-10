# Jenkins OSS Auto Upload Utils

自动化部署工具，用于将网站静态资源自动上传到对象存储服务（OSS），支持多云平台S3兼容存储。

## 功能特性

- 🚀 **全自动化流程**: Jenkins Pipeline自动触发，无需人工干预
- ☁️ **多云平台支持**: 支持 AWS S3、阿里云OSS、腾讯云COS等S3兼容存储
- 📦 **自动解压**: 自动解压zip压缩包并上传所有文件
- 📧 **邮件通知**: 部署完成后自动发送详细的部署报告邮件
- 📊 **详细日志**: 完整的上传日志和统计信息
- 🔒 **安全可靠**: 使用密码参数类型保护敏感信息

## 目录结构

```
jenkins-utils/
├── Jenkinsfile              # Jenkins Pipeline配置文件
├── upload_to_oss.py         # Python上传脚本
├── requirements.txt         # Python依赖
├── .gitignore              # Git忽略文件配置
├── README.md               # 项目文档
├── QUICKSTART.md           # 快速入门指南
├── config.example.env      # 配置示例文件
└── test-setup.sh           # 本地测试脚本
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

3. **测试本地环境**（可选）:
   ```bash
   ./test-setup.sh
   ```
   该脚本会自动检查环境并创建测试文件，便于本地测试上传功能。

4. **在Jenkins中创建Pipeline任务**:
   - 新建Pipeline类型的任务
   - 在Pipeline配置中选择"Pipeline script from SCM"
   - 配置Git仓库地址
   - 指定Jenkinsfile路径

### 配置说明

#### Pipeline参数

| 参数名称 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| DOWNLOAD_URLS | Text | * | 下载zip文件的URL列表（多个URL用逗号分隔）|
| ZIP_FILE_PATH | String | * | 本地zip文件路径（仅在DOWNLOAD_URLS为空时使用） |
| S3_BUCKET | String | ✓ | S3存储桶名称 |
| S3_PREFIX | String |  | S3路径前缀（文件夹路径） |
| CLOUD_PROVIDER | Choice | ✓ | 云服务提供商（aws/aliyun/tencent） |
| S3_ENDPOINT | String | ** | S3端点URL（阿里云和腾讯云必填） |
| S3_REGION | String | ✓ | S3区域（默认：us-east-1） |
| EMAIL_RECIPIENTS | String | ✓ | 邮件接收人（多个用逗号分隔） |
| SMTP_SERVER | String | ✓ | SMTP服务器地址 |
| SMTP_PORT | String | ✓ | SMTP端口（默认：587） |
| SMTP_USERNAME | String | ✓ | SMTP用户名 |
| SMTP_PASSWORD | Password | ✓ | SMTP密码 |
| AWS_ACCESS_KEY_ID | Password | ✓ | 访问密钥ID |
| AWS_SECRET_ACCESS_KEY | Password | ✓ | 访问密钥 |

\* DOWNLOAD_URLS 和 ZIP_FILE_PATH 二选一，优先使用 DOWNLOAD_URLS  
\*\* S3_ENDPOINT 对于非AWS云服务商是必填的

#### 资源来源模式

**模式1：URL下载模式（推荐）**
- 在DOWNLOAD_URLS参数中输入一个或多个zip文件的URL（用逗号分隔）
- 流水线会自动下载、解压并上传所有资源
- 示例：`https://example.com/static-v1.zip,https://example.com/static-v2.zip`

**模式2：本地文件模式**
- 在ZIP_FILE_PATH参数中输入本地zip文件的完整路径
- 流水线会解压并上传该文件
- 仅在DOWNLOAD_URLS为空时使用

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

#### 方式1: 在Jenkins UI中触发（URL下载模式）

1. 打开Jenkins Pipeline任务
2. 点击"Build with Parameters"
3. 在DOWNLOAD_URLS参数中输入zip文件的URL（多个URL用逗号分隔）
4. 填写其他必要参数（留空ZIP_FILE_PATH）
5. 点击"Build"开始构建

**示例URL参数：**
```
https://cdn.example.com/releases/website-v1.0.0.zip,https://cdn.example.com/releases/assets-v1.0.0.zip
```

#### 方式2: 在Jenkins UI中触发（本地文件模式）

1. 打开Jenkins Pipeline任务
2. 点击"Build with Parameters"
3. 留空DOWNLOAD_URLS参数
4. 在ZIP_FILE_PATH参数中输入本地zip文件路径
5. 填写其他必要参数
6. 点击"Build"开始构建

#### 方式3: 命令行执行（URL下载模式）

```bash
python3 upload_to_oss.py \
  --download-urls "https://cdn.example.com/static-v1.zip,https://cdn.example.com/static-v2.zip" \
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

#### 方式4: 命令行执行（本地目录模式）

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

### URL下载模式
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
│ 下载ZIP文件(URL)│
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

1. **使用密码参数类型**:
   - 当前实现使用Jenkins的密码参数类型（password）来保护敏感信息
   - 密码参数在Jenkins界面中会被掩码显示
   - 如需更高安全性，可将Jenkinsfile中的参数引用改为使用Jenkins凭证存储

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
