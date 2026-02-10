import {
  BeefInput as BeefInput300,
  BeefOutput as BeefOutput300,
  calculateBeef as calculateBeef300,
} from "@aginnovationaustralia/emissions-calculators3.0.0";
import {
  BeefInput as BeefInput301,
  BeefOutput as BeefOutput301,
  calculateBeef as calculateBeef301,
} from "@aginnovationaustralia/emissions-calculators3.0.1";

const beefRequest: BeefInput300 = {
  state: "qld",
  northOfTropicOfCapricorn: true,
  rainfallAbove600: true,
  beef: [
    {
      id: "beef_cattle_001",
      classes: {
        bullsGt1: {
          autumn: {
            head: 50,
            liveweight: 450,
            liveweightGain: 0.5,
            crudeProtein: 15,
            dryMatterDigestibility: 0.6,
          },
          spring: {
            head: 50,
            liveweight: 450,
            liveweightGain: 0.5,
            crudeProtein: 15,
            dryMatterDigestibility: 0.6,
          },
          summer: {
            head: 50,
            liveweight: 450,
            liveweightGain: 0.5,
            crudeProtein: 15,
            dryMatterDigestibility: 0.6,
          },
          winter: {
            head: 50,
            liveweight: 450,
            liveweightGain: 0.5,
            crudeProtein: 15,
            dryMatterDigestibility: 0.6,
          },
          headSold: 25,
          saleWeight: 500,
        },
      },
      cottonseedFeed: 10,

      limestone: 10,
      limestoneFraction: 0.8,
      fertiliser: {
        singleSuperphosphate: 5,
        pastureDryland: 10,
        pastureIrrigated: 2,
        cropsDryland: 8,
        cropsIrrigated: 1,
      },
      mineralSupplementation: {
        mineralBlock: 2,
        mineralBlockUrea: 0.3,
        weanerBlock: 1,
        weanerBlockUrea: 0.2,
        drySeasonMix: 1.5,
        drySeasonMixUrea: 0.25,
      },
      cowsCalving: {
        spring: 0.2,
        summer: 0.1,
        autumn: 0.5,
        winter: 0.2,
      },
      diesel: 0,
      petrol: 0,
      lpg: 0,
      electricitySource: "State Grid",
      electricityRenewable: 0,
      electricityUse: 0,
      grainFeed: 0,
      hayFeed: 0,
      herbicide: 0,
      herbicideOther: 0,
    },
  ],
  burning: [],
  vegetation: [],
};

// These 2 versions have no changes between their input or output types, the same input object can be used for both.
// In future versions this won't always be true.
const beefResponse300: BeefOutput300 = calculateBeef300(beefRequest);
const beefResponse301: BeefOutput301 = calculateBeef301(beefRequest);

// If you want a single function that can accept multiple input versions, you can use a generic type like this
// Over time the inputs and outputs of each version will diverge more and more.
function calculateBeefWithVersion<
  V extends "3.0.0" | "3.0.1",
  I extends V extends "3.0.0" ? BeefInput300 : BeefInput301
>(version: V, input: I): V extends "3.0.0" ? BeefOutput300 : BeefOutput301 {
  if (version === "3.0.0") {
    return calculateBeef300(input);
  } else {
    return calculateBeef301(input);
  }
}
