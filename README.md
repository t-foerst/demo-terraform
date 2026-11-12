# demo-terraform

Terraform-Code für die AWS-Infrastruktur meiner Bachelorarbeit „GitOps-basierte vs. pipelinebasierte Deployments in Kubernetes“ (TH Köln, 2026). Auf dem hier erzeugten Amazon-EKS-Cluster laufen dieselbe Anwendung einmal per GitHub-Actions-Pipeline und einmal per Argo CD (GitOps), um beide Ansätze unter gleichen Bedingungen zu vergleichen.

| Repo | Inhalt |
|---|---|
| **demo-terraform** (dieses) | AWS-Infrastruktur: VPC, EKS, RDS, IAM, DNS/TLS |
| [demo-kubernetes](https://github.com/t-foerst/demo-kubernetes) | Kubernetes-Manifeste: Load Balancer Controller, Argo CD, External Secrets, App je Deploy-Weg |
| [demo-app](https://github.com/t-foerst/demo-app) | Beispielanwendung (Node.js + PostgreSQL) inkl. CI/CD-Pipeline |

## Ressourcen

| Datei | Inhalt |
|---|---|
| `vpc.tf` | VPC `10.0.0.0/16` über 2 Availability Zones (`eu-central-1a/b`), öffentliche und private Subnetze, je AZ ein NAT Gateway |
| `eks.tf` | EKS-Cluster (Kubernetes 1.31, Modul `terraform-aws-modules/eks`) mit Managed Node Group aus 4 × `t3.small`; IRSA-Rolle für den AWS Load Balancer Controller |
| `rds.tf` | PostgreSQL 16 auf RDS (`db.t4g.micro`) in den privaten Subnetzen, Zugriff nur aus dem Cluster; Master-Passwort wird von RDS in **AWS Secrets Manager** verwaltet |
| `iam.tf` | GitHub-OIDC-Provider und Rolle `github-actions-deploy` für die Pipeline (keine statischen AWS-Keys in GitHub), EKS Access Entry mit `AmazonEKSEditPolicy`; IRSA-Rolle für den External Secrets Operator mit Leserecht auf genau das DB-Secret |
| `dns.tf` | ACM-Zertifikat für die App-Hostnamen, DNS-Validierung und CNAMEs auf den ALB über Cloudflare |
| `outputs.tf` | Werte, die nach jedem Aufbau in `demo-kubernetes` bzw. als GitHub-Variable in `demo-app` eingetragen werden (VPC-ID, Zertifikats-ARN, Secret-ARN, Rollen-ARNs) |

## Nutzung

```bash
cat > terraform.tfvars <<EOF   # gitignored
cloudflare_api_token = "<token mit Zone:DNS:Edit auf foerst.haus>"
EOF

terraform init
terraform apply
$(terraform output -raw configure_kubectl)   # kubeconfig setzen
```

Danach geht es mit der Checkliste in [demo-kubernetes](https://github.com/t-foerst/demo-kubernetes#checkliste-nach-cluster-neustart) weiter. Sobald der ALB existiert, dessen Hostnamen als `alb_hostname` setzen und erneut `terraform apply` ausführen, damit die CNAMEs angelegt werden.

Der Cluster wird nur für Messungen hochgefahren und danach mit `terraform destroy` wieder abgebaut (die NAT Gateways und der Cluster kosten auch im Leerlauf).

## Testergebnisse

`test-results/` enthält zwei Vorversuche aus dem Praxisprojekt, das der Bachelorarbeit vorausging:

- `hpa-test/`: Lasttest mit `hey` (50 parallele Clients, 4 Minuten) gegen die App und Skalierung durch den Horizontal Pod Autoscaler, inkl. Auswertungsskript und Plot
- `node-ausfall-test/`: Erreichbarkeit der App, während ein Worker-Node terminiert wird
