# AWS EC2 + Kinesis Firehose + S3 Pipeline

Este proyecto automatiza la creación de una pipeline de datos en AWS que genera logs de e-commerce, los envía a través de Kinesis Firehose y los almacena en S3.

## Arquitectura

```
EC2 Instance (LogGenerator) → Kinesis Agent → Firehose → S3 Bucket
```

## Requisitos

- Python 3.x
- boto3: `pip install boto3`
- AWS CLI configurado con credenciales (`aws configure`)
- Cuenta AWS (todos los recursos son Free Tier elegibles)

## Configuración Importante

**ANTES DE EJECUTAR**: Edita los scripts y cambia el nombre del bucket para que sea único globalmente:

```python
# En create_bucket.py y create_firehose.py
BUCKET_NAME = 'ecom-purchaselogs-bucket-TU-ID-UNICO'  # Agrega tu ID de estudiante o timestamp
```

También verifica que la región sea la correcta en todos los scripts:
```python
REGION = 'us-east-2'  # Cambia si usas otra región
```

## Orden de Ejecución

### 1. Crear Key Pair
```bash
python create_key.py
```
- Crea el key pair `ecom_key` para SSH
- Descarga el archivo `ecom_key.pem`
- **Importante**: Guarda este archivo, lo necesitarás para conectarte a la instancia

### 2. Crear Bucket S3
```bash
python create_bucket.py
```
- Crea el bucket donde se almacenarán los logs

### 3. Crear Firehose Delivery Stream
```bash
python create_firehose.py
```
- Crea el rol IAM para Firehose
- Crea el delivery stream `Purchaselogs`
- Configura el destino S3

### 4. Crear Rol IAM para EC2
```bash
python create_ec2_role.py
```
- Crea el rol con permisos para Kinesis Firehose
- Crea el instance profile necesario

### 5. Lanzar Instancia EC2
```bash
python create_instance.py
```
- Crea security group con SSH (puerto 22) y puerto 5000 abiertos
- Lanza instancia t3.micro con 8GB de almacenamiento
- Ejecuta `user_data.sh` para configurar automáticamente:
  - Instala Kinesis Agent
  - Descarga LogGenerator
  - Configura el agente para enviar logs a Firehose

## Verificación

### Conectarse a la instancia
```bash
chmod 400 ecom_key.pem
ssh -i ecom_key.pem ec2-user@<IP_PUBLICA>
```

Obtén la IP pública del output de `create_instance.py` o desde la consola AWS.

### Generar logs de prueba
```bash
cd /home/ec2-user/ecom
python LogGenerator.py
```

### Verificar que los logs lleguen a S3
1. Espera 5-10 minutos (el buffer de Firehose es de 5 minutos)
2. Ve a la consola de S3 o usa:
```bash
aws s3 ls s3://ecom-purchaselogs-bucket-TU-ID/logs/ --recursive
```

### Ver logs del Kinesis Agent
```bash
sudo tail -f /var/log/aws-kinesis-agent/aws-kinesis-agent.log
```

## Listar Recursos

Ver key pairs disponibles:
```bash
python list_key_pairs.py
```

## Limpieza (Importante para evitar costos)

**Elimina TODOS los recursos cuando termines:**
```bash
python cleanup_all.py
```

Este script elimina en orden:
1. Instancias EC2
2. Security groups
3. Firehose delivery stream
4. Bucket S3 (y todo su contenido)
5. Roles IAM

## Estructura de Archivos

```
.
├── create_key.py           # Crea key pair para SSH
├── list_key_pairs.py       # Lista key pairs existentes
├── create_bucket.py        # Crea bucket S3
├── create_firehose.py      # Crea Firehose y su rol IAM
├── create_ec2_role.py      # Crea rol IAM para EC2
├── create_instance.py      # Lanza instancia EC2
├── user_data.sh           # Script de inicialización de la instancia
├── cleanup_all.py         # Elimina todos los recursos
└── README.md              # Este archivo
```

## Troubleshooting

### Error: "InvalidKeyPair.NotFound"
- El key pair no existe en la región especificada
- Ejecuta `create_key.py` primero
- Verifica que la región sea la misma en todos los scripts

### Error: "BucketAlreadyExists"
- El nombre del bucket ya está en uso globalmente
- Cambia `BUCKET_NAME` a algo único

### No llegan logs a S3
- Verifica que el Kinesis Agent esté corriendo: `sudo service aws-kinesis-agent status`
- Revisa los logs: `sudo tail -f /var/log/aws-kinesis-agent/aws-kinesis-agent.log`
- Verifica que el delivery stream exista: `aws firehose describe-delivery-stream --delivery-stream-name Purchaselogs --region us-east-2`
- Espera al menos 5 minutos (buffer de Firehose)

### Error: "UnauthorizedOperation" al crear instancia
- Tu usuario IAM no tiene permisos suficientes
- Necesitas permisos para EC2, IAM, S3, y Firehose

### La instancia no se conecta por SSH
- Verifica que el security group tenga el puerto 22 abierto
- Verifica que estés usando el key pair correcto
- Verifica que la instancia tenga IP pública asignada

## Costos Estimados

Con Free Tier:
- EC2 t3.micro: 750 horas/mes gratis
- S3: 5GB gratis
- Kinesis Firehose: Primeros 500GB gratis
- Transferencia de datos: Primeros 100GB gratis

**Importante**: Ejecuta `cleanup_all.py` cuando termines para evitar cargos.

## Conceptos Aprendidos

- Automatización de infraestructura con boto3
- Integración de servicios AWS
- IAM roles y policies
- Security groups y networking
- User data para bootstrapping
- Streaming de datos con Kinesis
- Buenas prácticas de limpieza de recursos
