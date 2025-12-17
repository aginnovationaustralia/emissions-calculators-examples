using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;

namespace EAP_Integration_Test
{
    // This class converts the more Linux / Unix-ey PKCS8 PEM format to the format that .NET prefers: PFX.
    // It is also possible to convert the certificates once using the following openssl command, then
    // just use this single file instead of reading two files and doing this conversion in the program itself:
    //
    // openssl pkcs12 -export -in my.crt -inkey my.key -out mycert.pfx
    //
    // You'll have to supply a password, which you can then pass to the X509Certificate2 constructor like so:
    // X509Certificate2 cert = new X509Certificate2("mycert.pfx","password");
    // 
    // If you do that, then you can just use the certificate you get from that single line instead of bringing in this class.

    class Utils {
        public static byte[]? GetPrivateKeyBytes(string pemString)
        {
            string header = "-----BEGIN PRIVATE KEY-----";
            string footer = "-----END PRIVATE KEY-----";

            int start = pemString.IndexOf(header) + header.Length;
            int end = pemString.IndexOf(footer, start) - start;

            return Convert.FromBase64String(pemString.Substring(start, end));
        }

        public static X509Certificate2 GetCertificateFromPEMPaths(string certificatePath, string keyPath)
        {
            X509Certificate2 certificate = new X509Certificate2(certificatePath);
            byte[]? keyBuffer = GetPrivateKeyBytes(File.ReadAllText(keyPath));

            using var rsa = RSA.Create();
            rsa.ImportPkcs8PrivateKey(keyBuffer, out _);
            
            return new X509Certificate2(certificate.CopyWithPrivateKey(rsa).Export(X509ContentType.Pfx));
        }
    }

}