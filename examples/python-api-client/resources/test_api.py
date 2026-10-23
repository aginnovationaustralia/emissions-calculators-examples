#!/usr/bin/env python3
"""
Test script for the AIA Calculator API client
This script demonstrates how to use the generated API client locally
"""

import openapi_client
from openapi_client.rest import ApiException
from pprint import pprint

def create_valid_beef_input():
    """Create a valid beef input using from_dict methods"""

    # Sample data for a single beef herd, matching the PostBeefRequest model.
    # Most numeric inputs are wrapped as {"value": number}.
    beef_data = {
      "isFebruaryInLeapYear": False,
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
          "isInLeachingZone": False,
          "excludedFromNaturalWater": False,
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

    beef_input = openapi_client.PostBeefRequest.from_dict(beef_data)
    return beef_input

def test_beef_api():
    """Test the beef API endpoint with valid input"""
    
    configuration = openapi_client.Configuration(
        host="https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta",
        cert_file="cert.pem",
        key_file="key.pem",
    )

    # Create a valid beef input
    beef_input = create_valid_beef_input()
    
    print("Created beef input:")
    print("=" * 50)
    pprint(beef_input.to_dict())
    print("=" * 50)

    with openapi_client.ApiClient(configuration) as api_client:
        api_instance = openapi_client.EmissionsCalculatorsApi(api_client)

        try:
            print("Calling beef API...")
            api_response = api_instance.post_beef(beef_input)
            print("The response of EmissionsCalculatorsApi->post_beef:\n")
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling EmissionsCalculatorsApi->post_beef: %s\n" % e)
            print("This is expected if you don't have proper authentication configured")

def main():
    """Main function to run API tests"""
    print("Testing AIA Calculator API Client")
    print("=" * 40)
    
    # Test beef endpoint
    test_beef_api()
    print("\n" + "=" * 40)
    
    print("API testing complete!")
    print("\nNote: Authentication errors are expected if you haven't configured")
    print("proper credentials for the production API endpoint.")

if __name__ == "__main__":
    main()
