#!/bin/sh
# Create X.509 certificates for MongoDB for testing purposes
# Created following the appendices of the MongoDB Security Manual:
# https://www.mongodb.com/docs/manual/appendix/security/
set -ex

# Some configuration
DN_server="/C=NO/ST=Trondelag/L=Trondheim/O=SINTEF/OU=Team4.0 CA Server/CN=DataSpaces-Entities"
DN_client="/C=NO/ST=Trondelag/L=Trondheim/O=SINTEF/OU=Team4.0 Client/CN=DataSpaces-Entities"
DNS_server_1="mongodb"
DNS_server_2="localhost"

if [ -z "${HOST_USER}" ]; then
    echo "HOST_USER is not set. This means that the script will be run with 'root' user in a Docker container!"
fi

ORIGINAL_DIR=$(pwd)
TARGET_DIR=${ORIGINAL_DIR}
# if [ -z "${IN_DOCKER}" ] || [ -z "${CI}" ]; then
#     TARGET_DIR=${ORIGINAL_DIR}
# else
#     # Running through Docker Compose
#     TARGET_DIR=/mongo_tls
# fi

echo "Generating certificates in ${TARGET_DIR}"
mkdir -p ${TARGET_DIR}

# Run in a temporary directory
mkdir -p /tmp/mongodb-test
cd /tmp/mongodb-test

## 1. Create a CA Certificate
# OpenSSL Configuration File
cat > openssl-test-ca.cnf <<EOF
# NOT FOR PRODUCTION USE. OpenSSL configuration file for testing.

# For the CA policy
[ policy_match ]
countryName = match
stateOrProvinceName = match
organizationName = match
organizationalUnitName = optional
commonName = supplied
emailAddress = optional

[ req ]
default_bits = 4096
default_keyfile = myTestCertificateKey.pem    ## The default private key file name.
default_md = sha256                           ## Use SHA-256 for Signatures
distinguished_name = req_dn
req_extensions = v3_req
x509_extensions = v3_ca # The extensions to add to the self signed cert

[ v3_req ]
subjectKeyIdentifier  = hash
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
nsComment = "OpenSSL Generated Certificate for TESTING only.  NOT FOR PRODUCTION USE."
extendedKeyUsage  = serverAuth, clientAuth

[ req_dn ]
countryName = Country Name (2 letter code)
countryName_default =
countryName_min = 2
countryName_max = 2

stateOrProvinceName = State or Province Name (full name)
stateOrProvinceName_default = TestCertificateStateName
stateOrProvinceName_max = 64

localityName = Locality Name (eg, city)
localityName_default = TestCertificateLocalityName
localityName_max = 64

organizationName = Organization Name (eg, company)
organizationName_default = TestCertificateOrgName
organizationName_max = 64

organizationalUnitName = Organizational Unit Name (eg, section)
organizationalUnitName_default = TestCertificateOrgUnitName
organizationalUnitName_max = 64

commonName = Common Name (eg, YOUR name)
commonName_max = 64

[ v3_ca ]
# Extensions for a typical CA

subjectKeyIdentifier=hash
basicConstraints = critical,CA:true
authorityKeyIdentifier=keyid:always,issuer:always
EOF

# Test CA PEM file
openssl genrsa -out mongodb-test-ca.key 4096
openssl req -new -x509 -days 1826 -key mongodb-test-ca.key -out mongodb-test-ca.crt -config openssl-test-ca.cnf -subj "${DN_server}"

openssl genrsa -out mongodb-test-ia.key 4096
openssl req -new -key mongodb-test-ia.key -out mongodb-test-ia.csr -config openssl-test-ca.cnf -subj "${DN_server}"
openssl x509 -sha256 -req -days 730 -in mongodb-test-ia.csr -CA mongodb-test-ca.crt -CAkey mongodb-test-ca.key -set_serial 01 -out mongodb-test-ia.crt -extfile openssl-test-ca.cnf -extensions v3_ca

cat mongodb-test-ia.crt mongodb-test-ca.crt > test-ca.pem

## 2. Create a Server Certificate
# OpenSSL Configuration File
cat > openssl-test-server.cnf <<EOF
# NOT FOR PRODUCTION USE. OpenSSL configuration file for testing.


[ req ]
default_bits = 4096
default_keyfile = myTestServerCertificateKey.pem    ## The default private key file name.
default_md = sha256
distinguished_name = req_dn
req_extensions = v3_req

[ v3_req ]
subjectKeyIdentifier  = hash
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
nsComment = "OpenSSL Generated Certificate for TESTING only.  NOT FOR PRODUCTION USE."
extendedKeyUsage  = serverAuth, clientAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = ${DNS_server_1}
DNS.2 = ${DNS_server_2}

[ req_dn ]
countryName = Country Name (2 letter code)
countryName_default = TestServerCertificateCountry
countryName_min = 2
countryName_max = 2

stateOrProvinceName = State or Province Name (full name)
stateOrProvinceName_default = TestServerCertificateState
stateOrProvinceName_max = 64

localityName = Locality Name (eg, city)
localityName_default = TestServerCertificateLocality
localityName_max = 64

organizationName = Organization Name (eg, company)
organizationName_default = TestServerCertificateOrg
organizationName_max = 64

organizationalUnitName = Organizational Unit Name (eg, section)
organizationalUnitName_default = TestServerCertificateOrgUnit
organizationalUnitName_max = 64

commonName = Common Name (eg, YOUR name)
commonName_max = 64
EOF

# Test PEM file for Server
openssl genrsa -out mongodb-test-server1.key 4096
openssl req -new -key mongodb-test-server1.key -out mongodb-test-server1.csr -config openssl-test-server.cnf -subj "${DN_server}"
openssl x509 -sha256 -req -days 365 -in mongodb-test-server1.csr -CA mongodb-test-ia.crt -CAkey mongodb-test-ia.key -CAcreateserial -out mongodb-test-server1.crt -extfile openssl-test-server.cnf -extensions v3_req
cat mongodb-test-server1.crt mongodb-test-server1.key > test-server1.pem

## 3. Create a Client Certificate
# OpenSSL Configuration File
cat > openssl-test-client.cnf <<EOF
# NOT FOR PRODUCTION USE. OpenSSL configuration file for testing.

[ req ]
default_bits = 4096
default_keyfile = myTestClientCertificateKey.pem    ## The default private key file name.
default_md = sha256
distinguished_name = req_dn
req_extensions = v3_req


[ v3_req ]
subjectKeyIdentifier  = hash
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
nsComment = "OpenSSL Generated Certificate for TESTING only.  NOT FOR PRODUCTION USE."
extendedKeyUsage  = serverAuth, clientAuth


[ req_dn ]
countryName = Country Name (2 letter code)
countryName_default =
countryName_min = 2
countryName_max = 2

stateOrProvinceName = State or Province Name (full name)
stateOrProvinceName_default = TestClientCertificateState
stateOrProvinceName_max = 64

localityName = Locality Name (eg, city)
localityName_default = TestClientCertificateLocality
localityName_max = 64

organizationName = Organization Name (eg, company)
organizationName_default = TestClientCertificateOrg
organizationName_max = 64

organizationalUnitName = Organizational Unit Name (eg, section)
organizationalUnitName_default = TestClientCertificateOrgUnit
organizationalUnitName_max = 64
commonName = Common Name (eg, YOUR name)
commonName_max = 64
EOF

openssl genrsa -out mongodb-test-client.key 4096
openssl req -new -key mongodb-test-client.key -out mongodb-test-client.csr -config openssl-test-client.cnf -subj "${DN_client}"
openssl x509 -sha256 -req -days 365 -in mongodb-test-client.csr -CA mongodb-test-ia.crt -CAkey mongodb-test-ia.key -CAcreateserial -out mongodb-test-client.crt -extfile openssl-test-client.cnf -extensions v3_req
cat mongodb-test-client.crt mongodb-test-client.key > test-client.pem

# Remove temporary files
mv -fZ *.pem ${TARGET_DIR}
cd ${TARGET_DIR}
rm -rf /tmp/mongodb-test

# Update ownership of files
if [ -n "${HOST_USER}" ]; then
    chown -R ${HOST_USER}:${HOST_USER} ${TARGET_DIR}
fi
