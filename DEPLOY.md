# Deploying to AWS (App Runner)

> These steps were **not executed by the author of this template**; run them yourself, and record what actually happens (screenshots, service URL, CloudWatch graphs) in the README once it works. Only claim "deployed on AWS" after you have done it.

**Cost control first:** create an AWS Budget alert (e.g. $5) and plan to delete the service after recording a demo.

1. **Push the image to ECR** (replace `<acct>` and `<region>`):
   ```bash
   aws ecr create-repository --repository-name finrisk-service --region <region>
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
   docker build -t finrisk-service .
   docker tag finrisk-service:latest <acct>.dkr.ecr.<region>.amazonaws.com/finrisk-service:latest
   docker push <acct>.dkr.ecr.<region>.amazonaws.com/finrisk-service:latest
   ```
2. **Create the service** in the AWS console: App Runner, source = Amazon ECR image above, port `8000`, health check protocol HTTP path `/health`, smallest instance size.
3. **Verify:** `curl https://<service-url>/health` and `/screen?theme=cyber`.
4. **Monitor:** App Runner publishes application logs (your JSON lines) to CloudWatch Logs and service metrics (request count, latency, 4xx/5xx) to CloudWatch Metrics. Create two alarms: 5xx count and p95 request latency. Screenshot the dashboard.
5. **Note:** the Prometheus `/metrics` endpoint and `alerts.yml` apply to the docker-compose setup; on App Runner use the CloudWatch metrics above.
6. **Tear down** after the demo: delete the App Runner service and the ECR repository.

Once done, add the real service name, region and a screenshot to the README, then ask for the CV line to be upgraded.
