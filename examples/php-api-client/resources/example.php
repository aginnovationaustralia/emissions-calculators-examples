<?php
require_once(__DIR__ . '/vendor/autoload.php');

use OpenAPI\Client\Api\EmissionsCalculatorsApi;
use OpenAPI\Client\ObjectSerializer;
use GuzzleHttp\Client;
use OpenAPI\Client\Configuration;

try {
    // Sample data for a single beef herd, matching the PostBeefRequest schema.
    // The PHP generator flattens oneOf types into a single model, which cannot represent
    // alternatives such as seasonal vs monthly cattle classes. So the request is described as JSON
    // and sent as-is; the generated client still handles mTLS, transport and the typed response.
    // Most numeric inputs are wrapped as { "value": number }.
    $beefJson = <<<'JSON'
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
JSON;

    $request = json_decode($beefJson, false, 512, JSON_THROW_ON_ERROR);

    // Configure API
    $config = Configuration::getDefaultConfiguration();
    $config->setHost('https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta');
    $config->setCertFile(__DIR__ . '/cert.pem');
    $config->setKeyFile(__DIR__ . '/key.pem');

    // Initialize API
    $api = new EmissionsCalculatorsApi(new Client(), $config);

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
