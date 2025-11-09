# Quick Start Guide

这是一个快速入门指南，帮助您在5分钟内完成基本配置。

## 步骤 1: 准备环境

### 安装依赖
```bash
pip3 install -r requirements.txt
```

### 验证安装
```bash
python3 upload_to_oss.py --help
```

## 步骤 2: 准备测试文件

创建一个包含静态网站文件的zip压缩包：

```bash
# 示例：创建测试网站
mkdir -p /tmp/website
echo "<html><body>Hello World</body></html>" > /tmp/website/index.html
echo "body { margin: 0; }" > /tmp/website/style.css

# 压缩文件
cd /tmp
zip -r website.zip website/
```

## 步骤 3: 配置云存储

根据您使用的云平台，准备以下信息：

### AWS S3
- Bucket名称
- Access Key ID 和 Secret Access Key
- Region (如: us-east-1)

### 阿里云OSS
- Bucket名称
- Access Key ID 和 Access Key Secret
- Endpoint (如: https://oss-cn-hangzhou.aliyuncs.com)
- Region (如: cn-hangzhou)

### 腾讯云COS
- Bucket名称 (格式: bucket-name-appid)
- Secret ID 和 Secret Key
- Endpoint (如: https://cos.ap-guangzhou.myqcloud.com)
- Region (如: ap-guangzhou)

## 步骤 4: 配置邮件服务

准备SMTP邮件服务信息：

### Gmail 示例
```
SMTP Server: smtp.gmail.com
Port: 587
Username: your-email@gmail.com
Password: your-app-password (需要在Google账户设置中生成)
```

### QQ邮箱示例
```
SMTP Server: smtp.qq.com
Port: 587
Username: your-email@qq.com
Password: 授权码 (需要在QQ邮箱设置中生成)
```

### 163邮箱示例
```
SMTP Server: smtp.163.com
Port: 465 或 25
Username: your-email@163.com
Password: 授权码 (需要在163邮箱设置中生成)
```

## 步骤 5: 测试运行

### 命令行测试

使用以下命令测试上传功能（替换为实际值）：

```bash
python3 upload_to_oss.py \
  --source-dir /tmp/website \
  --bucket YOUR_BUCKET_NAME \
  --prefix test/upload \
  --provider aliyun \
  --endpoint https://oss-cn-hangzhou.aliyuncs.com \
  --region cn-hangzhou \
  --access-key YOUR_ACCESS_KEY \
  --secret-key YOUR_SECRET_KEY \
  --email-recipients your-email@example.com \
  --smtp-server smtp.gmail.com \
  --smtp-port 587 \
  --smtp-username your-email@gmail.com \
  --smtp-password YOUR_APP_PASSWORD
```

### Jenkins Pipeline测试

1. 在Jenkins中创建新的Pipeline任务
2. 配置Pipeline脚本来源为"Pipeline script from SCM"
3. 填写Git仓库地址: `https://github.com/kukukikits/jenkins-utils.git`
4. 点击"Build with Parameters"
5. 填写所有参数
6. 点击"Build"开始测试

## 步骤 6: 验证结果

### 检查上传
登录云存储控制台，确认文件已成功上传到指定路径。

### 检查邮件
查收邮箱，应该收到一封包含上传统计信息的部署报告邮件。

### 检查日志
查看以下日志文件了解详细信息：
- Jenkins Console Output（在Jenkins任务页面）
- `oss_upload.log`（在工作目录中）

## 常见问题

### 1. 认证失败
**问题**: `NoCredentialsError` 或 `Access Denied`

**解决方案**:
- 确认Access Key和Secret Key正确
- 检查密钥是否有上传权限
- 对于阿里云/腾讯云，确认endpoint URL正确

### 2. 连接超时
**问题**: `Connection timeout` 或 `Unable to connect`

**解决方案**:
- 检查网络连接
- 确认endpoint URL格式正确
- 检查防火墙规则

### 3. 邮件发送失败
**问题**: `SMTP authentication failed`

**解决方案**:
- 使用App Password而不是账户密码（Gmail）
- 使用授权码而不是账户密码（QQ、163）
- 确认SMTP服务器和端口正确

### 4. 文件未上传
**问题**: 文件未出现在OSS中

**解决方案**:
- 检查bucket名称是否正确
- 确认有足够的存储空间
- 查看日志文件了解具体错误

## 下一步

- 阅读完整的 [README.md](README.md) 了解更多功能
- 查看 [config.example.env](config.example.env) 了解配置示例
- 根据需求自定义 Jenkinsfile

## 获取帮助

如果遇到问题：
1. 查看日志文件 `oss_upload.log`
2. 检查Jenkins Console Output
3. 提交Issue: https://github.com/kukukikits/jenkins-utils/issues
