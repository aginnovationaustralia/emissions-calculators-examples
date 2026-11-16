<?php
require_once(__DIR__ . '/vendor/autoload.php');

use OpenAPI\Client\Api\EmissionsCalculatorsApi;
use OpenAPI\Client\ObjectSerializer;
use GuzzleHttp\Client;
use OpenAPI\Client\Configuration;
use OpenAPI\Client\Model\PostBeefRequest;

try {
    // Sample data for a single beef herd, matching the PostBeefRequest schema. It is written as
    // JSON for readability and deserialized into the generated models below, which resolves each
    // oneOf (e.g. seasonal vs monthly cattle classes) to its concrete type.
    // Most numeric inputs are wrapped as { "value": number }.
    $beefJson = <<<'JSON'
{
    "isFebruaryInLeapYear": false,
    "electricity": {
        "method": "location",
        "electricityPurchasedKilowattHours": {
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
                        "fractionCowsThisSeasonInCalf": {
                            "value": 0.2
                        },
                        "fractionCowsPreviousSeasonInCalf": {
                            "value": 0.2
                        }
                    },
                    "summer": {
                        "head": {
                            "value": 50
                        },
                        "fractionCowsThisSeasonInCalf": {
                            "value": 0.1
                        },
                        "fractionCowsPreviousSeasonInCalf": {
                            "value": 0.2
                        }
                    },
                    "autumn": {
                        "head": {
                            "value": 50
                        },
                        "fractionCowsThisSeasonInCalf": {
                            "value": 0.5
                        },
                        "fractionCowsPreviousSeasonInCalf": {
                            "value": 0.1
                        }
                    },
                    "winter": {
                        "head": {
                            "value": 50
                        },
                        "fractionCowsThisSeasonInCalf": {
                            "value": 0.2
                        },
                        "fractionCowsPreviousSeasonInCalf": {
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
            "liveweightSoldKilograms": {
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
                        "massAppliedKilograms": {
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
                "areaManagedHectares": {
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
                    "amountTonnes": {
                        "value": 2
                    }
                }
            ],
            "chemicals": [
                {
                    "type": "Herbicide (paraquat, diquat, glyphosate)",
                    "amountKilograms": {
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
                            "massAppliedKilograms": {
                                "value": 2000
                            },
                            "massPurchasedKilograms": {
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
JSON;

    $request = ObjectSerializer::deserialize(
        json_decode($beefJson, false, 512, JSON_THROW_ON_ERROR),
        PostBeefRequest::class
    );

    // Configure API
    $config = Configuration::getDefaultConfiguration();
    $config->setHost('https://emissionscalculator-mtls.production.aiaapi.com/veerg/1.1-beta');

    // Initialize API, authenticating via mTLS with the client certificate and key
    $client = new Client([
        'cert' => __DIR__ . '/cert.pem',
        'ssl_key' => __DIR__ . '/key.pem',
    ]);
    $api = new EmissionsCalculatorsApi($client, $config);

    echo "Calling beef API...\n";
    echo "================================\n";

    // Make the API call
    $result = $api->postBeef($request);

    // Print the result
    echo "Success! API call completed.\n\n";
    echo "Net emissions (tonnes CO2e): " . json_encode(ObjectSerializer::sanitizeForSerialization($result->getNet())) . "\n";

    echo "\n================================\n";
    echo "API call complete!\n";

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
    echo "File: " . $e->getFile() . "\n";
    echo "Line: " . $e->getLine() . "\n";
}
