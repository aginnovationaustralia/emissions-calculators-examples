using System.Net.Http.Headers;
using System.Net.Security;
using System.Security.Authentication;
using System.Security.Cryptography.X509Certificates;
using EAP_Integration_Test;

X509Certificate2 clientCertificate = Utils.GetCertificateFromPEMPaths(Path.Join("certificates", "my-certificate.crt"), Path.Join("certificates", "my-private-key.key"));
Func<HttpRequestMessage, X509Certificate2?, X509Chain?, SslPolicyErrors, bool> ValidateServerCertificate = (sender, certificate, chain, sslPolicyErrors) => {
    if (certificate == null) return false;
    if (certificate.NotBefore > DateTime.Now || certificate.NotAfter < DateTime.Now)
    {
        Console.WriteLine("Server certificate is expired or not yet valid");
        return false;
    }

    if (certificate.Subject != "CN=*.aiaapi.com") 
    {
        Console.WriteLine("Server certificate is not issued for *.aiaapi.com");
        return false;
    }

    if (!certificate.Verify()) {
        Console.WriteLine("Server certificate did not pass verify check.");
        return false;
    }

    return true;
};

// Create an HttpClient with MTLS authentication
HttpClient httpClient = new HttpClient(new HttpClientHandler
{
    ClientCertificateOptions = ClientCertificateOption.Manual,
    SslProtocols = SslProtocols.Tls12,
    ServerCertificateCustomValidationCallback = ValidateServerCertificate,
    ClientCertificates = { clientCertificate },
});
httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
httpClient.DefaultRequestHeaders.Add("User-Agent", "EAP Integration Tester 1.0");

// Send the API request
HttpResponseMessage response = httpClient.PostAsync("https://emissionscalculator-mtls.production.aiaapi.com/calculator/v1/sheepbeef", ExampleRequest.content).Result;

Console.WriteLine("Got Response:");
Console.Write(response.Content.ReadAsStringAsync().Result);
