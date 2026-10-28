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
using System.Text.Json;

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

        static PostBeefRequest CreateValidBeefInput(JsonSerializerOptions jsonOptions)
        {
            // Create sample data for a single beef herd.
            // The request contains deeply nested oneOf types, so it is easiest to describe it as JSON
            // and deserialise it into the generated PostBeefRequest model using the client's serializer options.
            // Most numeric inputs are wrapped as { "value": number }.
            var beefJson = """
            {
              "isFebruaryInLeapYear": false,
              "electricity": {
                "method": "location",
                "electricityPurchasedKWh": {
                  "value": 5000
                },
                "region": "QLD"
              },
              "herds": [
                {
                  "id": "beef_cattle_001",
                  "electricityAllocation": {
                    "value": 1
                  },
                  "region": "QLD - Moderate/High",
                  "classes": {
                    "period": "seasonal",
                    "cowsGt3Years": {
                      "spring": {
                        "head": {
                          "value": 50
                        },
                        "proportionCowsThisSeasonInCalf": {
                          "value": 0.2
                        },
                        "proportionCowsPreviousSeasonInCalf": {
                          "value": 0.2
                        }
                      },
                      "summer": {
                        "head": {
                          "value": 50
                        },
                        "proportionCowsThisSeasonInCalf": {
                          "value": 0.1
                        },
                        "proportionCowsPreviousSeasonInCalf": {
                          "value": 0.2
                        }
                      },
                      "autumn": {
                        "head": {
                          "value": 50
                        },
                        "proportionCowsThisSeasonInCalf": {
                          "value": 0.5
                        },
                        "proportionCowsPreviousSeasonInCalf": {
                          "value": 0.1
                        }
                      },
                      "winter": {
                        "head": {
                          "value": 50
                        },
                        "proportionCowsThisSeasonInCalf": {
                          "value": 0.2
                        },
                        "proportionCowsPreviousSeasonInCalf": {
                          "value": 0.5
                        }
                      }
                    }
                  },
                  "breed": "Northern Brahman cross breed",
                  "grazingSystem": "Non-irrigated pasture",
                  "climateZone": "Tropical dry",
                  "isInLeachingZone": false,
                  "excludedFromNaturalWater": false,
                  "liveweightSoldKg": {
                    "value": 12500
                  },
                  "fuel": {
                    "transport": [
                      {
                        "vehicleType": "Cars and light commercial vehicles",
                        "fuelType": "Diesel oil",
                        "amountKilolitres": {
                          "value": 1
                        }
                      }
                    ],
                    "stationary": []
                  },
                  "lime": {
                    "applications": [
                      {
                        "type": "Limestone",
                        "massAppliedKg": {
                          "value": 10000
                        },
                        "limestoneFraction": {
                          "value": 0.8
                        }
                      }
                    ]
                  },
                  "pasture": {
                    "type": "Perennial pasture",
                    "areaManaged": {
                      "value": 500
                    },
                    "fractionOfAnnualCropBurnt": {
                      "value": 0
                    },
                    "residues": {
                      "calculationMethod": "1"
                    }
                  },
                  "purchasedLivestock": [],
                  "purchasedFeed": [],
                  "purchasedMineralSupplements": [
                    {
                      "type": "Lick block, dry season mix",
                      "amount": {
                        "value": 2
                      }
                    }
                  ],
                  "chemicals": [
                    {
                      "type": "Herbicide (paraquat, diquat, glyphosate)",
                      "amountKg": {
                        "value": 50
                      }
                    }
                  ],
                  "services": {
                    "fuel": {
                      "transport": [],
                      "stationary": []
                    }
                  },
                  "fertiliser": {
                    "productionSystem": "Non-irrigated pasture",
                    "inorganic": {
                      "calculationMethodScope1": "1",
                      "applications": [
                        {
                          "fertiliserType": "Urea",
                          "massAppliedKg": {
                            "value": 2000
                          },
                          "calculationMethodScope3": "1"
                        }
                      ]
                    },
                    "organic": {
                      "applications": []
                    }
                  }
                }
              ]
            }
            """;

            return JsonSerializer.Deserialize<PostBeefRequest>(beefJson, jsonOptions)
                ?? throw new InvalidOperationException("Could not create beef input");
        }

        static async Task TestBeefApi()
        {
            // Load client certificate for mTLS
            var certPath = "./cert.pem";
            var keyPath = "./key.pem";
            X509Certificate2? clientCertificate = null;
            try
            {
                clientCertificate = Utils.GetCertificateFromPEMPaths(certPath, keyPath);
            }
            catch (Exception e)
            {
                Console.WriteLine($"Error reading certificate files: {e.Message}");
                Console.WriteLine("Continuing without certificates - authentication will fail");
            }

            // Create host builder with API configuration
            Action<HostBuilderContext, HostConfiguration> configureApi = (context, options) =>
            {
                options.AddApiHttpClients(
                    client =>
                    {
                        // Set base address
                        client.BaseAddress = new Uri("https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta");
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
            var api = host.Services.GetRequiredService<IEmissionsCalculatorsApi>();

            // Create a valid beef input
            var jsonOptions = host.Services.GetRequiredService<JsonSerializerOptionsProvider>().Options;
            var beefInput = CreateValidBeefInput(jsonOptions);

            Console.WriteLine("Created beef input:");
            Console.WriteLine("=".PadRight(50, '='));
            Console.WriteLine(JsonSerializer.Serialize(beefInput, jsonOptions));
            Console.WriteLine("=".PadRight(50, '='));
            Console.WriteLine();

            try
            {
                Console.WriteLine("Calling beef API...");
                var apiResponse = await api.PostBeefAsync(beefInput);
                
                Console.WriteLine("The response of EmissionsCalculatorsApi->PostBeefAsync:");
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
                Console.WriteLine($"Exception when calling EmissionsCalculatorsApi->PostBeefAsync: {e.Message}");
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

