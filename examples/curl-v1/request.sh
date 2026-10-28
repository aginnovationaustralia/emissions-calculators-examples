#! /bin/bash

# This script makes a request to the EAP API using curl and the certificate (certificate.pem) and key (private.key).

# It is not recommended to use cURL for a production integration with the EAP, but it can be useful for testing and debugging.
# If requests made with cURL are successful, then your certificate and key are working correctly.

curl -X POST https://emissionscalculator-mtls.production.aiaapi.com/calculator/v1/feedlot \
     --key private.key \
     --cert certificate.pem \
     -H "Content-Type: application/json" \
     -d '{
            "state": "nsw",
            "feedlots": [
                {
                    "system": "Drylot",
                    "groups": [
                        {
                            "stays": [
                                {
                                    "livestock": 1.1,
                                    "stayAverageDuration": 1.1,
                                    "liveweight": 1.1,
                                    "dryMatterDigestibility": 1.1,
                                    "crudeProtein": 1.1,
                                    "nitrogenRetention": 1.1,
                                    "dailyIntake": 1.1,
                                    "ndf": 1.1,
                                    "etherExtract": 1.1
                                }
                            ]
                        }
                    ],
                    "fertiliser": {
                        "singleSuperphosphate": 1.1,
                        "pastureDryland": 1.1,
                        "pastureIrrigated": 1.1,
                        "cropsDryland": 1.1,
                        "cropsIrrigated": 1.1
                    },
                    "purchases": {},
                    "sales": {
                        "bullsGt1": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "bullsGt1Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "steersLt1": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "steersLt1Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "steers1To2": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "steers1To2Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "steersGt2": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "steersGt2Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "cowsGt2": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "cowsGt2Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "heifersLt1": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "heifersLt1Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "heifers1To2": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "heifers1To2Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "heifersGt2": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ],
                        "heifersGt2Traded": [
                            {
                                "head": 1.1,
                                "saleWeight": 1.1
                            }
                        ]
                    },
                    "diesel": 1.1,
                    "petrol": 1.1,
                    "lpg": 1.1,
                    "electricitySource": "State Grid",
                    "electricityRenewable": 1.1,
                    "electricityUse": 1.1,
                    "grainFeed": 1.1,
                    "hayFeed": 1.1,
                    "cottonseedFeed": 1.1,
                    "herbicide": 1.1,
                    "herbicideOther": 1.1,
                    "distanceCattleTransported": 1.1,
                    "truckType": "4 Deck Trailer",
                    "limestone": 1.1,
                    "limestoneFraction": 1.1
                }
            ],
            "vegetation": [
                {
                    "vegetation": {
                        "region": "South West",
                        "treeSpecies": "Mixed species (Environmental Plantings)",
                        "soil": "Loams & Clays",
                        "area": 1.1,
                        "age": 1.1
                    },
                    "feedlotProportion": [
                        1.1
                    ]
                }
            ]
        }'
