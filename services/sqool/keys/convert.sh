#!/bin/bash
echo This script convert certificates exported from Keychain Access
echo to the format that Python SSL library has support
# development
CERT_FILE=aps-9.cer
PRIVATE_KEY=CertificatesAPNPentaCenter.p12
OUT_CERT_FILE=${CERT_FILE%.cer}.pem
OUT_PRIVATE_KEY=${PRIVATE_KEY%.p12}.pem
# production 
#CERT_FILE=aps_production.cer
#PRIVATE_KEY=apn_production_provider_private.p12
#OUT_CERT_FILE=${CERT_FILE%.cer}.pem
#OUT_PRIVATE_KEY=${PRIVATE_KEY%.p12}.pem
openssl x509 -in $CERT_FILE -inform der -out $OUT_CERT_FILE
echo Set some temporary password first
openssl pkcs12 -nocerts -out $OUT_PRIVATE_KEY.pass -in $PRIVATE_KEY
openssl rsa -in $OUT_PRIVATE_KEY.pass -out $OUT_PRIVATE_KEY
rm $OUT_PRIVATE_KEY.pass
echo 'conversion completed:'
echo cert = $OUT_CERT_FILE
echo private = $OUT_PRIVATE_KEY

