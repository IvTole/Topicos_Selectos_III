#!/bin/bash

# Instalar aws kinesis agent
sudo yum install -y aws-kinesis-agent

# Crear carpeta /ecom en /home con ruta absoluta
mkdir -p /home/ec2-user/ecom
cd /home/ec2-user/ecom

# Bajar scripts de python para datos ficticios de e commerce
wget http://media.sundog-soft.com/AWSBigData/LogGenerator.zip
unzip LogGenerator.zip

# Cambiar permisos de script
chmod a+x LogGenerator.py

# Ajustar ownership para ec2-user
chown -R ec2-user:ec2-user /home/ec2-user/ecom

# Crear carpeta donde van a ir los datos
sudo mkdir -p /var/log/cadabra
sudo chown ec2-user:ec2-user /var/log/cadabra

# Configurar Kinesis Agent
sudo cat > /etc/aws-kinesis/agent.json << 'EOF'
{
  "cloudwatch.emitMetrics": true,
  "kinesis.endpoint": "",
  "firehose.endpoint": "firehose.us-east-2.amazonaws.com",

  "flows": [
    {
      "filePattern": "/var/log/cadabra/*.log",
      "deliveryStream": "Purchaselogs"
    }
  ]
}
EOF

# Iniciar el servicio de Kinesis Agent
sudo service aws-kinesis-agent start
sudo chkconfig aws-kinesis-agent on


