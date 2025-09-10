#!/bin/bash
# Script para configurar monitoramento e alertas no Google Cloud

echo "=== Configuração de Monitoramento e Alertas ==="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Nenhum projeto configurado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Projeto: ${PROJECT_ID}${NC}"
echo ""

# Habilita APIs necessárias
echo -e "${YELLOW}📋 Habilitando APIs de monitoramento...${NC}"
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable clouderrorreporting.googleapis.com
gcloud services enable cloudtrace.googleapis.com

echo ""

# Cria notification channel (email)
echo -e "${YELLOW}📧 Configurando notificações por email...${NC}"
read -p "Email para receber alertas: " NOTIFICATION_EMAIL

# Cria o notification channel
NOTIFICATION_CHANNEL=$(gcloud alpha monitoring channels create \
    --display-name="Quiz App Alerts" \
    --type=email \
    --channel-labels=email_address=${NOTIFICATION_EMAIL} \
    --format="value(name)")

echo -e "${GREEN}✅ Canal de notificação criado: ${NOTIFICATION_CHANNEL}${NC}"

# Cria policy de alerta para alta taxa de erro
echo -e "${YELLOW}🚨 Criando alerta para alta taxa de erro...${NC}"
cat > error_rate_policy.json << EOF
{
  "displayName": "Quiz App - Alta Taxa de Erro",
  "documentation": {
    "content": "Taxa de erro da aplicação Quiz App está muito alta",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Taxa de erro > 5%",
      "conditionThreshold": {
        "filter": "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/response_count\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_SUM",
            "groupByFields": ["resource.label.module_id"]
          }
        ],
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.05,
        "duration": "300s"
      }
    }
  ],
  "notificationChannels": ["${NOTIFICATION_CHANNEL}"],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF

gcloud alpha monitoring policies create --policy-from-file=error_rate_policy.json
rm error_rate_policy.json

# Cria policy de alerta para alta latência
echo -e "${YELLOW}⏱️  Criando alerta para alta latência...${NC}"
cat > latency_policy.json << EOF
{
  "displayName": "Quiz App - Alta Latência",
  "documentation": {
    "content": "Latência da aplicação Quiz App está muito alta",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Latência > 2 segundos",
      "conditionThreshold": {
        "filter": "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/response_latencies\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_MEAN",
            "crossSeriesReducer": "REDUCE_MEAN"
          }
        ],
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 2000,
        "duration": "300s"
      }
    }
  ],
  "notificationChannels": ["${NOTIFICATION_CHANNEL}"],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF

gcloud alpha monitoring policies create --policy-from-file=latency_policy.json
rm latency_policy.json

# Cria dashboard personalizado
echo -e "${YELLOW}📊 Criando dashboard personalizado...${NC}"
cat > dashboard.json << EOF
{
  "displayName": "Quiz App Dashboard",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Requests por Minuto",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/request_count\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE"
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "widget": {
          "title": "Latência Média",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/response_latencies\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN"
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "width": 12,
        "height": 4,
        "yPos": 4,
        "widget": {
          "title": "Taxa de Erro",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/response_count\"",
                    "aggregation": {
                      "alignmentPeriod": "300s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM",
                      "groupByFields": ["response_code_class"]
                    }
                  }
                }
              }
            ]
          }
        }
      }
    ]
  }
}
EOF

DASHBOARD_URL=$(gcloud monitoring dashboards create --config-from-file=dashboard.json --format="value(name)")
rm dashboard.json

echo -e "${GREEN}✅ Dashboard criado${NC}"

# Configura log-based metrics
echo -e "${YELLOW}📝 Configurando métricas baseadas em logs...${NC}"

# Métrica para logins de admin
gcloud logging metrics create admin_logins \
    --description="Contagem de logins de admin" \
    --log-filter='resource.type="gae_app" AND textPayload:"admin_logged_in"'

# Métrica para erros da aplicação
gcloud logging metrics create app_errors \
    --description="Contagem de erros da aplicação" \
    --log-filter='resource.type="gae_app" AND severity>=ERROR'

echo ""
echo -e "${GREEN}✅ Monitoramento configurado com sucesso!${NC}"
echo ""
echo -e "${BLUE}📋 Recursos criados:${NC}"
echo "• Canal de notificação por email"
echo "• Alerta para alta taxa de erro"
echo "• Alerta para alta latência"
echo "• Dashboard personalizado"
echo "• Métricas baseadas em logs"
echo ""
echo -e "${BLUE}🔗 Links úteis:${NC}"
echo "• Dashboard: https://console.cloud.google.com/monitoring/dashboards"
echo "• Alertas: https://console.cloud.google.com/monitoring/alerting"
echo "• Logs: https://console.cloud.google.com/logs"
echo "• Error Reporting: https://console.cloud.google.com/errors"
echo ""
echo -e "${YELLOW}⚠️  Importante:${NC}"
echo "• Configure o billing para receber notificações de custos"
echo "• Revise os alertas periodicamente"
echo "• Monitore o dashboard regularmente"