#!/usr/bin/env node
/**
 * Test script for the AIA Calculator API client
 * This script demonstrates how to use the generated API client locally
 */

import * as fs from 'fs';
import * as https from 'https';
import { Configuration, GAFApi } from './index';
import {
    PostBeefRequest,
    PostBeefRequestBeefInner,
    PostBeefRequestBeefInnerClasses,
    PostBeefRequestBeefInnerClassesBullsGt1Autumn,
    PostBeefRequestBeefInnerClassesCowsGt2,
    PostBeefRequestBeefInnerCowsCalving,
    PostBeefRequestBeefInnerElectricitySourceEnum,
    PostBeefRequestBeefInnerFertiliser,
    PostBeefRequestBeefInnerMineralSupplementation,
    PostBeefRequestStateEnum
} from './models';

function createValidBeefInput(): PostBeefRequest {
    /**
     * Create a valid beef input using the generated model classes
     * This structure matches PostBeefRequest model requirements
     */
    
    // Create seasonal data for cows greater than 2 years old
    const springSeason: PostBeefRequestBeefInnerClassesBullsGt1Autumn = {
        head: 50,  // number of animals
        liveweight: 450,  // average kg/head
        liveweightGain: 0.5  // kg/day
        // crudeProtein and dryMatterDigestibility are optional
    };
    
    const summerSeason: PostBeefRequestBeefInnerClassesBullsGt1Autumn = {
        head: 50,
        liveweight: 440,
        liveweightGain: 0.3
    };
    
    const autumnSeason: PostBeefRequestBeefInnerClassesBullsGt1Autumn = {
        head: 50,
        liveweight: 460,
        liveweightGain: 0.4
    };
    
    const winterSeason: PostBeefRequestBeefInnerClassesBullsGt1Autumn = {
        head: 50,
        liveweight: 450,
        liveweightGain: 0.4
    };
    
    // Create cows greater than 2 years old class
    const cowsGt2: PostBeefRequestBeefInnerClassesCowsGt2 = {
        spring: springSeason,
        summer: summerSeason,
        autumn: autumnSeason,
        winter: winterSeason,
        headSold: 25,  // required: number sold
        saleWeight: 500  // required: weight at sale in kg/head
        // headPurchased, purchasedWeight, source, and purchases are optional
    };
    
    // Create classes object
    const classes: PostBeefRequestBeefInnerClasses = {
        cowsGt2: cowsGt2
    };
    
    // Create fertiliser data
    const fertiliser: PostBeefRequestBeefInnerFertiliser = {
        singleSuperphosphate: 5.0,
        pastureDryland: 10.0,
        pastureIrrigated: 2.0,
        cropsDryland: 8.0,
        cropsIrrigated: 1.0
        // otherDryland, otherIrrigated, otherType, and otherFertilisers are optional
    };
    
    // Create mineral supplementation data
    const mineralSupplementation: PostBeefRequestBeefInnerMineralSupplementation = {
        mineralBlock: 2.0,
        mineralBlockUrea: 0.3,
        weanerBlock: 1.0,
        weanerBlockUrea: 0.2,
        drySeasonMix: 1.5,
        drySeasonMixUrea: 0.25
    };
    
    // Create cows calving data
    const cowsCalving: PostBeefRequestBeefInnerCowsCalving = {
        spring: 0.2,
        summer: 0.1,
        autumn: 0.5,
        winter: 0.2
    };
    
    // Create beef enterprise
    const beefEnterprise: PostBeefRequestBeefInner = {
        id: "beef_cattle_001",
        classes: classes,
        limestone: 10.0,
        limestoneFraction: 0.8,  // Fraction between 0 and 1
        fertiliser: fertiliser,
        diesel: 1000,
        petrol: 200,
        lpg: 100,
        mineralSupplementation: mineralSupplementation,
        electricitySource: PostBeefRequestBeefInnerElectricitySourceEnum.StateGrid,  // Must be 'State Grid' or 'Renewable'
        electricityRenewable: 0.2,  // Fraction between 0 and 1
        electricityUse: 5000,  // kWh
        grainFeed: 10.0,  // tonnes
        hayFeed: 5.0,
        cottonseedFeed: 2.0,
        herbicide: 50.0,  // kg
        herbicideOther: 20.0,
        cowsCalving: cowsCalving
    };
    
    // Create the main request
    const beefRequest: PostBeefRequest = {
        state: PostBeefRequestStateEnum.Qld,  // Queensland (must be valid enum)
        northOfTropicOfCapricorn: true,
        rainfallAbove600: true,
        beef: [beefEnterprise],
        burning: [],  // List of burning activities (optional)
        vegetation: []  // List of vegetation activities (optional)
    };
    
    return beefRequest;
}

async function testBeefApi(): Promise<void> {
    /**
     * Test the beef API endpoint with valid input
     */
    
    const basePath = "https://emissionscalculator-mtls.staging.aiaapi.com/calculator/3.0.0";
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
    const apiInstance = new GAFApi(configuration);
    
    // Create a valid beef input
    const beefInput = createValidBeefInput();
    
    console.log("Created beef input:");
    console.log("=".repeat(50));
    console.log(JSON.stringify(beefInput, null, 2));
    console.log("=".repeat(50));
    
    try {
        console.log("Calling beef API...");
        const apiResponse = await apiInstance.postBeef({ postBeefRequest: beefInput });
        console.log("The response of GAFApi->postBeef:\n");
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
            console.error(`Exception when calling GAFApi->postBeef: ${error.message || error}`);
            console.error(`Status code: ${response.status}`);
            console.error(`Response body: ${bodyText}`);
        } else {
            console.error(`Exception when calling GAFApi->postBeef: ${error}`);
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


