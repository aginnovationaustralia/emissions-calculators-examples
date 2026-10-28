#!/usr/bin/env node
/**
 * Test script for the AIA Calculator API client
 * This script demonstrates how to use the generated API client locally
 */

import * as fs from 'fs';
import * as https from 'https';
import { Configuration, EmissionsCalculatorsApi } from './index';
import {
    AgrochemicalType,
    BasicCropProductionSystem,
    BasicProductionSystemScope1Method1,
    BeefBreed,
    BeefClassesWithSeasonalInput,
    BeefClassWithCalvesSeasonalInput,
    CarsAndLightCommercialVehicles,
    CarsLightCommercialFuelType,
    ClimateZoneOrZoneType,
    ElectricityRegion,
    FuelInput,
    GrazingProductionSystemWithRainfall,
    InorganicFertiliserType,
    LimeAmeliorant,
    LimestoneOrDolomiteApplication,
    LocationBased,
    Method11,
    PastureType,
    PostBeefRequest,
    PostBeefRequestHerdsInner,
    PostBeefRequestHerdsInnerChemicalsInner,
    PostBeefRequestHerdsInnerPasture,
    PurchasedMineralSupplementType,
    StateOrRegion,
} from './models';

function createValidBeefInput(): PostBeefRequest {
    /**
     * Create a valid beef input for a single beef herd, built up from the generated models.
     * Each part is typed with its model, so the compiler checks it as it is built. Fields with
     * a fixed set of values use the generated enums (e.g. StateOrRegion). Fields that only select
     * a oneOf variant (e.g. period: 'seasonal') are string literals, which are also type checked.
     * Most numeric inputs are wrapped as { value: number }.
     */

    // Cows over 3 years old, with head counts and calving rates for each season
    const cowsGt3Years: BeefClassWithCalvesSeasonalInput = {
        spring: {
            head: { value: 50 },
            proportionCowsThisSeasonInCalf: { value: 0.2 },
            proportionCowsPreviousSeasonInCalf: { value: 0.2 },
        },
        summer: {
            head: { value: 50 },
            proportionCowsThisSeasonInCalf: { value: 0.1 },
            proportionCowsPreviousSeasonInCalf: { value: 0.2 },
        },
        autumn: {
            head: { value: 50 },
            proportionCowsThisSeasonInCalf: { value: 0.5 },
            proportionCowsPreviousSeasonInCalf: { value: 0.1 },
        },
        winter: {
            head: { value: 50 },
            proportionCowsThisSeasonInCalf: { value: 0.2 },
            proportionCowsPreviousSeasonInCalf: { value: 0.5 },
        },
    };

    const classes: BeefClassesWithSeasonalInput = {
        period: 'seasonal',
        cowsGt3Years,
    };

    const dieselCar: CarsAndLightCommercialVehicles = {
        vehicleType: 'Cars and light commercial vehicles',
        fuelType: CarsLightCommercialFuelType.DieselOil,
        amountKilolitres: { value: 1 },
    };
    const fuel: FuelInput = {
        transport: [dieselCar],
        stationary: [],
    };

    const limestone: LimestoneOrDolomiteApplication = {
        type: LimeAmeliorant.Limestone,
        massAppliedKg: { value: 10000 },
        limestoneFraction: { value: 0.8 },
    };

    const pasture: PostBeefRequestHerdsInnerPasture = {
        type: PastureType.PerennialPasture,
        areaManaged: { value: 500 },
        fractionOfAnnualCropBurnt: { value: 0 },
        residues: { calculationMethod: '1' },
    };

    const lickBlock: Method11 = {
        type: PurchasedMineralSupplementType.LickBlockDrySeasonMix,
        amount: { value: 2 },
    };

    const herbicide: PostBeefRequestHerdsInnerChemicalsInner = {
        type: AgrochemicalType.HerbicideParaquatDiquatGlyphosate,
        amountKg: { value: 50 },
    };

    const fertiliser: BasicProductionSystemScope1Method1 = {
        productionSystem: BasicCropProductionSystem.NonIrrigatedPasture,
        inorganic: {
            calculationMethodScope1: '1',
            applications: [
                {
                    fertiliserType: InorganicFertiliserType.Urea,
                    massAppliedKg: { value: 2000 },
                    calculationMethodScope3: '1',
                },
            ],
        },
        organic: { applications: [] },
    };

    const herd: PostBeefRequestHerdsInner = {
        id: 'beef_cattle_001',
        electricityAllocation: { value: 1 },
        region: StateOrRegion.QldModerateHigh,
        classes,
        breed: BeefBreed.NorthernBrahmanCrossBreed,
        grazingSystem: GrazingProductionSystemWithRainfall.NonIrrigatedPasture,
        climateZone: ClimateZoneOrZoneType.TropicalDry,
        isInLeachingZone: false,
        excludedFromNaturalWater: false,
        liveweightSoldKg: { value: 12500 },
        fuel,
        lime: { applications: [limestone] },
        pasture,
        purchasedLivestock: [],
        purchasedFeed: [],
        purchasedMineralSupplements: [lickBlock],
        chemicals: [herbicide],
        services: { fuel: { transport: [], stationary: [] } },
        fertiliser,
    };

    const electricity: LocationBased = {
        method: 'location',
        electricityPurchasedKWh: { value: 5000 },
        region: ElectricityRegion.Qld,
    };

    return {
        isFebruaryInLeapYear: false,
        electricity,
        herds: [herd],
    };
}

async function testBeefApi(): Promise<void> {
    /**
     * Test the beef API endpoint with valid input
     */
    
    const basePath = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/4.0-beta";
    const certFile = "cert.pem";
    const keyFile = "key.pem";
    
    // Read certificate and key files for mTLS
    let cert: Buffer | undefined;
    let key: Buffer | undefined;
    try {
        cert = fs.readFileSync(certFile);
        key = fs.readFileSync(keyFile);
    } catch (error) {
        console.error(`Error reading certificate files: ${error}`);
        console.log("Continuing without certificates - authentication will fail");
    }
    
    // Create a custom fetch function that supports mTLS
    const customFetch = (url: string, init?: RequestInit): Promise<Response> => {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(url);
            
            const options: https.RequestOptions = {
                hostname: urlObj.hostname,
                port: urlObj.port || 443,
                path: urlObj.pathname + urlObj.search,
                method: init?.method || 'GET',
                headers: init?.headers as Record<string, string>,
                cert: cert,
                key: key,
                rejectUnauthorized: true
            };
            
            const req = https.request(options, (res) => {
                const chunks: Buffer[] = [];
                
                res.on('data', (chunk) => {
                    chunks.push(chunk);
                });
                
                res.on('end', () => {
                    const body = Buffer.concat(chunks);
                    const response = new Response(body, {
                        status: res.statusCode,
                        statusText: res.statusMessage,
                        headers: res.headers as HeadersInit
                    });
                    resolve(response);
                });
            });
            
            req.on('error', (error) => {
                reject(error);
            });
            
            if (init?.body) {
                if (typeof init.body === 'string') {
                    req.write(init.body);
                } else if (Buffer.isBuffer(init.body)) {
                    req.write(init.body);
                } else {
                    req.write(JSON.stringify(init.body));
                }
            }
            
            req.end();
        });
    };
    
    // Create configuration with custom fetch for mTLS and headers
    const configuration = new Configuration({
        basePath: basePath,
        fetchApi: customFetch as any,
        headers: {
            'User-Agent': 'AIA Calculator API Client Test Script',
            'Accept': 'application/json'
        }
    });
    
    // Create API instance with configuration
    const apiInstance = new EmissionsCalculatorsApi(configuration);
    
    // Create a valid beef input
    const beefInput = createValidBeefInput();
    
    console.log("Created beef input:");
    console.log("=".repeat(50));
    console.log(JSON.stringify(beefInput, null, 2));
    console.log("=".repeat(50));
    
    try {
        console.log("Calling beef API...");
        const apiResponse = await apiInstance.postBeef({ postBeefRequest: beefInput });
        console.log("The response of EmissionsCalculatorsApi->postBeef:\n");
        console.log(JSON.stringify(apiResponse, null, 2));
    } catch (error: any) {
        // Check if it's a ResponseError by checking for the response property
        if (error && error.response) {
            const response = error.response;
            let bodyText = '';
            try {
                bodyText = await response.text();
            } catch (e) {
                bodyText = 'Could not read response body';
            }
            console.error(`Exception when calling EmissionsCalculatorsApi->postBeef: ${error.message || error}`);
            console.error(`Status code: ${response.status}`);
            console.error(`Response body: ${bodyText}`);
        } else {
            console.error(`Exception when calling EmissionsCalculatorsApi->postBeef: ${error}`);
        }
        console.log("This is expected if you don't have proper authentication configured");
    }
}

async function main(): Promise<void> {
    /**
     * Main function to run API tests
     */
    console.log("Testing AIA Calculator API Client");
    console.log("=".repeat(40));
    
    // Test beef endpoint
    await testBeefApi();
    console.log("\n" + "=".repeat(40));
    
    console.log("API testing complete!");
    console.log("\nNote: Authentication errors are expected if you haven't configured");
    console.log("proper credentials for the production API endpoint.");
}

// Run the main function
main().catch((error) => {
    console.error("Unhandled error:", error);
    process.exit(1);
});


