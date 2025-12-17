using System.Text;

namespace EAP_Integration_Test
{
    class ExampleRequest {  
        // Normally this would be loaded / serialised from some kind of datasource, but for this example
        // we'll just hardcode the content.
        public static readonly StringContent content = new StringContent("""
{
  "state": "nsw",
  "northOfTropicOfCapricorn": true,
  "rainfallAbove600": true,
  "beef": {
    "classes": {
      "bullsGt1": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "steersLt1": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "steers1To2": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "steersGt2": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "cowsGt2": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "heifersLt1": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "heifers1To2": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "heifersGt2": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "steersGt2Traded": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "steers1To2Traded": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      },
      "steersLt1Traded": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0
        },
        "headPurchased": 0,
        "purchasedWeight": 0,
        "source": "Dairy origin",
        "headSold": 0,
        "saleWeight": 0,
        "livestockPurchases": [
          {
            "headPurchased": 0,
            "purchasedWeight": 0,
            "source": "Dairy origin"
          }
        ]
      }
    },
    "limestone": 0,
    "limestoneFraction": 0,
    "fertiliser": {
      "singleSuperphosphate": 0,
      "otherType": "Monoammonium phosphate (MAP)",
      "pastureDryland": 0,
      "pastureIrrigated": 0,
      "cropsDryland": 0,
      "cropsIrrigated": 0,
      "otherDryland": 0,
      "otherIrrigated": 0
    },
    "diesel": 0,
    "petrol": 0,
    "mineralSupplementation": {
      "mineralBlock": 0,
      "mineralBlockUrea": 0,
      "weanerBlock": 0,
      "weanerBlockUrea": 0,
      "drySeasonMix": 0,
      "drySeasonMixUrea": 0
    },
    "electricitySource": "State Grid",
    "electricityRenewable": 0,
    "electricityUse": 0,
    "grainFeed": 0,
    "hayFeed": 0,
    "cottonseedFeed": 0,
    "herbicide": 0,
    "herbicideOther": 0,
    "cowsCalving": {
      "spring": 0,
      "summer": 0,
      "autumn": 0,
      "winter": 0
    }
  },
  "sheep": {
    "classes": {
      "rams": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "wethers": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "maidenBreedingEwes": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "breedingEwes": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "otherEwes": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "eweLambs": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "wetherLambs": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "tradeLambsAndHoggets": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "tradeWethers": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      },
      "tradeEwes": {
        "autumn": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "winter": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "spring": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "summer": {
          "head": 0,
          "liveweight": 0,
          "liveweightGain": 0,
          "crudeProtein": 0,
          "dryMatterDigestibility": 0,
          "feedAvailability": 0
        },
        "headShorn": 0,
        "woolShorn": 0,
        "cleanWoolYield": 0,
        "headPurchased": 0,
        "purchasedWeight": 0,
        "headSold": 0,
        "saleWeight": 0
      }
    },
    "limestone": 0,
    "limestoneFraction": 0,
    "fertiliser": {
      "singleSuperphosphate": 0,
      "otherType": "Monoammonium phosphate (MAP)",
      "pastureDryland": 0,
      "pastureIrrigated": 0,
      "cropsDryland": 0,
      "cropsIrrigated": 0,
      "otherDryland": 0,
      "otherIrrigated": 0
    },
    "diesel": 0,
    "petrol": 0,
    "mineralSupplementation": {
      "mineralBlock": 0,
      "mineralBlockUrea": 0,
      "weanerBlock": 0,
      "weanerBlockUrea": 0,
      "drySeasonMix": 0,
      "drySeasonMixUrea": 0
    },
    "electricitySource": "State Grid",
    "electricityRenewable": 0,
    "electricityUse": 0,
    "grainFeed": 0,
    "hayFeed": 0,
    "herbicide": 0,
    "herbicideOther": 0,
    "merinoPercent": 0,
    "ewesLambing": {
      "autumn": 0,
      "winter": 0,
      "spring": 0,
      "summer": 0
    },
    "seasonalLambing": {
      "autumn": 0,
      "winter": 0,
      "spring": 0,
      "summer": 0
    }
  },
  "burning": {
    "fuel": "fine",
    "season": "early dry season",
    "patchiness": "low",
    "rainfallZone": "low",
    "yearsSinceLastFire": 0,
    "fireScarArea": 0,
    "vegetation": "Shrubland hummock"
  },
  "vegetation": [
    {
      "vegetation": {
        "region": "South West",
        "treeSpecies": "Mixed species (Environmental Plantings)",
        "soil": "Loams & Clays",
        "area": 0,
        "age": 0
      },
      "beefProportion": 0,
      "sheepProportion": 0
    }
  ]
}
""", Encoding.UTF8, "application/json");
    }
}