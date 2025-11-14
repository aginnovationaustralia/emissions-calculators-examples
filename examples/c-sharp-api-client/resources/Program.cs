using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Security;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Org.OpenAPITools.Api;
using Org.OpenAPITools.Client;
using Org.OpenAPITools.Extensions;
using Org.OpenAPITools.Model;
using System.Net.Http.Headers;

namespace TestApi
{
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

    class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("Testing AIA Calculator API Client");
            Console.WriteLine("=".PadRight(40, '='));
            Console.WriteLine();

            // Test beef endpoint
            await TestBeefApi();

            Console.WriteLine();
            Console.WriteLine("=".PadRight(40, '='));
            Console.WriteLine("API testing complete!");
            Console.WriteLine();
            Console.WriteLine("Note: Authentication errors are expected if you haven't configured");
            Console.WriteLine("proper credentials for the API endpoint.");
        }

        static PostBeefRequest CreateValidBeefInput()
        {
            // Create sample data for a beef cattle operation
            // This structure matches PostBeefRequest model requirements

            // Create seasonal data for cowsGt2
            var spring = new PostBeefRequestBeefInnerClassesBullsGt1Autumn(
                head: 50,
                liveweight: 450,
                liveweightGain: 0.5m
            );

            var summer = new PostBeefRequestBeefInnerClassesBullsGt1Autumn(
                head: 50,
                liveweight: 440,
                liveweightGain: 0.3m
            );

            var autumn = new PostBeefRequestBeefInnerClassesBullsGt1Autumn(
                head: 50,
                liveweight: 460,
                liveweightGain: 0.4m
            );

            var winter = new PostBeefRequestBeefInnerClassesBullsGt1Autumn(
                head: 50,
                liveweight: 450,
                liveweightGain: 0.4m
            );

            // Create cowsGt2 class
            var cowsGt2 = new PostBeefRequestBeefInnerClassesCowsGt2(
                autumn: autumn,
                winter: winter,
                spring: spring,
                summer: summer,
                headSold: 25,
                saleWeight: 500,
                // NOTE: This field is not required in the OpenAPI spec but there is a bug in the code generator for C#.
                // If it is undefined, the class fails to serialise to JSON
                source: PostBeefRequestBeefInnerClassesCowsGt2.SourceEnum.NthSthCentralQLD
            );

            // Create classes object
            var classes = new PostBeefRequestBeefInnerClasses(
                cowsGt2: new Option<PostBeefRequestBeefInnerClassesCowsGt2?>(cowsGt2)
            );

            // Create fertiliser
            var fertiliser = new PostBeefRequestBeefInnerFertiliser(
                singleSuperphosphate: 5.0m,
                pastureDryland: 10.0m,
                pastureIrrigated: 2.0m,
                cropsDryland: 8.0m,
                cropsIrrigated: 1.0m,
                // NOTE: This field is not required in the OpenAPI spec but there is a bug in the code generator for C#.
                // If it is undefined, the class fails to serialise to JSON
                otherType: PostBeefRequestBeefInnerFertiliser.OtherTypeEnum.MonoammoniumPhosphateMAP
            );

            // Create mineral supplementation
            var mineralSupplementation = new PostBeefRequestBeefInnerMineralSupplementation(
                mineralBlock: 2.0m,
                mineralBlockUrea: 0.3m,
                weanerBlock: 1.0m,
                weanerBlockUrea: 0.2m,
                drySeasonMix: 1.5m,
                drySeasonMixUrea: 0.25m
            );

            // Create cows calving
            var cowsCalving = new PostBeefRequestBeefInnerCowsCalving(
                spring: 0.2m,
                summer: 0.1m,
                autumn: 0.5m,
                winter: 0.2m
            );

            // Create beef inner
            var beefInner = new PostBeefRequestBeefInner(
                classes: classes,
                limestone: 10.0m,
                limestoneFraction: 0.8m,
                fertiliser: fertiliser,
                diesel: 1000m,
                petrol: 200m,
                lpg: 100m,
                mineralSupplementation: mineralSupplementation,
                electricitySource: PostBeefRequestBeefInner.ElectricitySourceEnum.StateGrid,
                electricityRenewable: 0.2m,
                electricityUse: 5000m,
                grainFeed: 10.0m,
                hayFeed: 5.0m,
                cottonseedFeed: 2.0m,
                herbicide: 50.0m,
                herbicideOther: 20.0m,
                cowsCalving: cowsCalving,
                id: new Option<string?>("beef_cattle_001")
            );

            // Create the main request
            var beefRequest = new PostBeefRequest(
                state: PostBeefRequest.StateEnum.Qld,
                northOfTropicOfCapricorn: true,
                rainfallAbove600: true,
                beef: new List<PostBeefRequestBeefInner> { beefInner },
                burning: new List<PostBeefRequestBurningInner>(),
                vegetation: new List<PostBeefRequestVegetationInner>()
            );

            return beefRequest;
        }

        static async Task TestBeefApi()
        {
            // Load client certificate for mTLS
            var certPath = "./cert.pem";
            var keyPath = "./key.pem";
            var clientCertificate = Utils.GetCertificateFromPEMPaths(certPath, keyPath);

            // Create host builder with API configuration
            Action<HostBuilderContext, IServiceCollection, HostConfiguration> configureApi = (context, services, options) =>
            {
                options.AddApiHttpClients(
                    client =>
                    {
                        // Set base address
                        client.BaseAddress = new Uri("https://emissionscalculator-mtls.staging.aiaapi.com/calculator/3.0.0");
                        client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
                        client.DefaultRequestHeaders.Add("User-Agent", "EAP Integration Tester 1.0");
                    },
                    builder =>
                    {
                        // Configure HttpClientHandler for mTLS
                        builder.ConfigurePrimaryHttpMessageHandler(() =>
                        {
                            var handler = new HttpClientHandler
                            {
                                ClientCertificateOptions = ClientCertificateOption.Manual,
                                SslProtocols = SslProtocols.Tls12
                            };

                            // Add client certificate if available
                            if (clientCertificate != null)
                            {
                                handler.ClientCertificates.Add(clientCertificate);
                            }

                            // Validate server certificate
                            handler.ServerCertificateCustomValidationCallback = (sender, certificate, chain, sslPolicyErrors) =>
                            {
                                if (certificate == null) return false;
                                if (certificate.NotBefore > DateTime.Now || certificate.NotAfter < DateTime.Now)
                                {
                                    Console.WriteLine("Server certificate is expired or not yet valid");
                                    return false;
                                }
                                
                                // Check Subject Alternative Name (SAN) extension for wildcard domain
                                // Wildcard certificates typically have the domain in SAN, not Subject CN
                                bool isValidDomain = false;
                                
                                // Check Subject CN
                                if (certificate.Subject.Contains("aiaapi.com"))
                                {
                                    isValidDomain = true;
                                }
                                
                                // Check SAN extension
                                foreach (var extension in certificate.Extensions)
                                {
                                    if (extension.Oid?.FriendlyName == "Subject Alternative Name" || 
                                        extension.Oid?.Value == "2.5.29.17")
                                    {
                                        var sanValue = extension.Format(false);
                                        if (sanValue.Contains("aiaapi.com"))
                                        {
                                            isValidDomain = true;
                                            break;
                                        }
                                    }
                                }
                                
                                if (!isValidDomain)
                                {
                                    Console.WriteLine($"Server certificate is not issued for *.aiaapi.com (Subject: {certificate.Subject})");
                                    return false;
                                }
                                
                                return true;
                            };

                            return handler;
                        });
                    }
                );
            };

            var hostBuilder = Host.CreateDefaultBuilder()
                .ConfigureApi(configureApi);

            var host = hostBuilder.Build();
            var api = host.Services.GetRequiredService<IGAFApi>();

            // Create a valid beef input
            var beefInput = CreateValidBeefInput();

            Console.WriteLine("Created beef input:");
            Console.WriteLine("=".PadRight(50, '='));
            Console.WriteLine(beefInput.ToString());
            Console.WriteLine("=".PadRight(50, '='));
            Console.WriteLine();

            try
            {
                Console.WriteLine("Calling beef API...");
                var apiResponse = await api.PostBeefAsync(beefInput);
                
                Console.WriteLine("The response of GAFApi->PostBeefAsync:");
                Console.WriteLine();
                
                if (apiResponse.Ok() != null)
                {
                    var response = apiResponse.Ok();
                    Console.WriteLine($"Response received successfully!");
                    Console.WriteLine($"Net emissions: {response.Net?.Total}");
                }
                else
                {
                    Console.WriteLine($"API call completed with status: {apiResponse.StatusCode}");
                    Console.WriteLine($"Reason: {apiResponse.ReasonPhrase}");
                }
            }
            catch (ApiException e)
            {
                Console.WriteLine($"Exception when calling GAFApi->PostBeefAsync: {e.Message}");
                Console.WriteLine("This is expected if you don't have proper authentication configured");
            }
            catch (Exception e)
            {
                Console.WriteLine($"Unexpected error: {e.Message}");
                Console.WriteLine(e.StackTrace);
            }
            finally
            {
                host.Dispose();
                clientCertificate?.Dispose();
            }
        }
    }
}

