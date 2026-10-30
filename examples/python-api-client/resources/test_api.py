#!/usr/bin/env python3
"""
Test script for the AIA Calculator API client
This script demonstrates how to use the generated API client locally
"""

import openapi_client
from openapi_client import (
    AgrochemicalType,
    BasicCropProductionSystem,
    BasicProductionSystemScope1Method1,
    BasicProductionSystemScope1Method1Inorganic,
    BasicProductionSystemScope1Method1InorganicApplicationsInner,
    BeefBreed,
    BeefClassesInput,
    BeefClassesWithSeasonalInput,
    BeefClassesWithSeasonalInputBullsLt1SpringHead,
    BeefClassWithCalvesSeasonalInput,
    BeefClassWithCalvesSeasonalInputAutumn,
    BeefClassWithCalvesSeasonalInputAutumnProportionCowsPreviousSeasonInCalf,
    BeefClassWithCalvesSeasonalInputAutumnProportionCowsThisSeasonInCalf,
    BeefClassWithCalvesSeasonalInputSpring,
    BeefClassWithCalvesSeasonalInputSpringProportionCowsPreviousSeasonInCalf,
    BeefClassWithCalvesSeasonalInputSpringProportionCowsThisSeasonInCalf,
    BeefClassWithCalvesSeasonalInputSummer,
    BeefClassWithCalvesSeasonalInputSummerProportionCowsPreviousSeasonInCalf,
    BeefClassWithCalvesSeasonalInputSummerProportionCowsThisSeasonInCalf,
    BeefClassWithCalvesSeasonalInputWinter,
    BeefClassWithCalvesSeasonalInputWinterProportionCowsPreviousSeasonInCalf,
    BeefClassWithCalvesSeasonalInputWinterProportionCowsThisSeasonInCalf,
    CarsAndLightCommercialVehicles,
    CarsAndLightCommercialVehiclesAmountKilolitres,
    CarsLightCommercialFuelType,
    ClimateZoneOrZoneType,
    ElectricityRegion,
    FertiliserInput,
    FuelInput,
    FuelInputTransportInner,
    GrazingProductionSystemWithRainfall,
    InorganicFertiliserType,
    LimeAmeliorant,
    LimestoneOrDolomiteApplication,
    LimestoneOrDolomiteApplicationLimestoneFraction,
    LimestoneOrDolomiteApplicationMassAppliedKg,
    LitresBasedFuel,
    LocationBased,
    LocationBasedElectricityPurchasedKWh,
    Method1,
    Method11,
    Method11Amount,
    OrganicFertilisersInput,
    PastureType,
    PostBeefRequest,
    PostBeefRequestElectricity,
    PostBeefRequestHerdsInner,
    PostBeefRequestHerdsInnerChemicalsInner,
    PostBeefRequestHerdsInnerChemicalsInnerAmountKg,
    PostBeefRequestHerdsInnerElectricityAllocation,
    PostBeefRequestHerdsInnerLime,
    PostBeefRequestHerdsInnerLimeApplicationsInner,
    PostBeefRequestHerdsInnerLiveweightSoldKg,
    PostBeefRequestHerdsInnerPasture,
    PostBeefRequestHerdsInnerPastureAreaManaged,
    PostBeefRequestHerdsInnerPastureFractionOfAnnualCropBurnt,
    PostBeefRequestHerdsInnerPastureResidues,
    PostBeefRequestHerdsInnerPurchasedMineralSupplementsInner,
    PostBeefRequestHerdsInnerServices,
    PurchasedMineralSupplementType,
    Scope3Method1,
    Scope3Method1MassAppliedKg,
    ServicesFuelInput,
    StateOrRegion,
)
from openapi_client.rest import ApiException
from pprint import pprint

def create_valid_beef_input():
    """Create a valid beef input using the generated model classes"""

    # Sample data for a single beef herd. Each oneOf in the schema has a wrapper model (e.g.
    # BeefClassesInput) that takes the chosen variant (e.g. BeefClassesWithSeasonalInput).
    # Fields with a fixed set of values use the generated enum classes (e.g. StateOrRegion).
    # Fields that only select a oneOf variant (e.g. period="seasonal", method="location") are
    # passed as strings, which the models check against the allowed value.
    # Most numeric inputs are wrapped in a model with a `value` field.
    cows_gt3_years = BeefClassWithCalvesSeasonalInput(
        spring=BeefClassWithCalvesSeasonalInputSpring(
            head=BeefClassesWithSeasonalInputBullsLt1SpringHead(value=50),
            proportion_cows_this_season_in_calf=BeefClassWithCalvesSeasonalInputSpringProportionCowsThisSeasonInCalf(value=0.2),
            proportion_cows_previous_season_in_calf=BeefClassWithCalvesSeasonalInputSpringProportionCowsPreviousSeasonInCalf(value=0.2),
        ),
        summer=BeefClassWithCalvesSeasonalInputSummer(
            head=BeefClassesWithSeasonalInputBullsLt1SpringHead(value=50),
            proportion_cows_this_season_in_calf=BeefClassWithCalvesSeasonalInputSummerProportionCowsThisSeasonInCalf(value=0.1),
            proportion_cows_previous_season_in_calf=BeefClassWithCalvesSeasonalInputSummerProportionCowsPreviousSeasonInCalf(value=0.2),
        ),
        autumn=BeefClassWithCalvesSeasonalInputAutumn(
            head=BeefClassesWithSeasonalInputBullsLt1SpringHead(value=50),
            proportion_cows_this_season_in_calf=BeefClassWithCalvesSeasonalInputAutumnProportionCowsThisSeasonInCalf(value=0.5),
            proportion_cows_previous_season_in_calf=BeefClassWithCalvesSeasonalInputAutumnProportionCowsPreviousSeasonInCalf(value=0.1),
        ),
        winter=BeefClassWithCalvesSeasonalInputWinter(
            head=BeefClassesWithSeasonalInputBullsLt1SpringHead(value=50),
            proportion_cows_this_season_in_calf=BeefClassWithCalvesSeasonalInputWinterProportionCowsThisSeasonInCalf(value=0.2),
            proportion_cows_previous_season_in_calf=BeefClassWithCalvesSeasonalInputWinterProportionCowsPreviousSeasonInCalf(value=0.5),
        ),
    )

    herd = PostBeefRequestHerdsInner(
        id="beef_cattle_001",
        electricity_allocation=PostBeefRequestHerdsInnerElectricityAllocation(value=1),
        region=StateOrRegion.QLD_MINUS__MODERATE_SLASH_HIGH,
        classes=BeefClassesInput(
            BeefClassesWithSeasonalInput(period="seasonal", cows_gt3_years=cows_gt3_years)
        ),
        breed=BeefBreed.NORTHERN_BRAHMAN_CROSS_BREED,
        grazing_system=GrazingProductionSystemWithRainfall.NON_MINUS_IRRIGATED_PASTURE,
        climate_zone=ClimateZoneOrZoneType.TROPICAL_DRY,
        is_in_leaching_zone=False,
        excluded_from_natural_water=False,
        liveweight_sold_kg=PostBeefRequestHerdsInnerLiveweightSoldKg(value=12500),
        fuel=FuelInput(
            transport=[
                FuelInputTransportInner(LitresBasedFuel(CarsAndLightCommercialVehicles(
                    vehicle_type="Cars and light commercial vehicles",
                    fuel_type=CarsLightCommercialFuelType.DIESEL_OIL,
                    amount_kilolitres=CarsAndLightCommercialVehiclesAmountKilolitres(value=1),
                )))
            ],
            stationary=[],
        ),
        lime=PostBeefRequestHerdsInnerLime(
            applications=[
                PostBeefRequestHerdsInnerLimeApplicationsInner(LimestoneOrDolomiteApplication(
                    type=LimeAmeliorant.LIMESTONE,
                    mass_applied_kg=LimestoneOrDolomiteApplicationMassAppliedKg(value=10000),
                    limestone_fraction=LimestoneOrDolomiteApplicationLimestoneFraction(value=0.8),
                ))
            ]
        ),
        pasture=PostBeefRequestHerdsInnerPasture(
            type=PastureType.PERENNIAL_PASTURE,
            area_managed=PostBeefRequestHerdsInnerPastureAreaManaged(value=500),
            fraction_of_annual_crop_burnt=PostBeefRequestHerdsInnerPastureFractionOfAnnualCropBurnt(value=0),
            residues=PostBeefRequestHerdsInnerPastureResidues(Method1(calculation_method="1")),
        ),
        purchased_livestock=[],
        purchased_feed=[],
        purchased_mineral_supplements=[
            PostBeefRequestHerdsInnerPurchasedMineralSupplementsInner(Method11(
                type=PurchasedMineralSupplementType.LICK_BLOCK_COMMA__DRY_SEASON_MIX,
                amount=Method11Amount(value=2),
            ))
        ],
        chemicals=[
            PostBeefRequestHerdsInnerChemicalsInner(
                type=AgrochemicalType.HERBICIDE_LEFT_PARENTHESIS_PARAQUAT_COMMA__DIQUAT_COMMA__GLYPHOSATE_RIGHT_PARENTHESIS,
                amount_kg=PostBeefRequestHerdsInnerChemicalsInnerAmountKg(value=50),
            )
        ],
        services=PostBeefRequestHerdsInnerServices(
            fuel=ServicesFuelInput(transport=[], stationary=[])
        ),
        fertiliser=FertiliserInput(BasicProductionSystemScope1Method1(
            production_system=BasicCropProductionSystem.NON_MINUS_IRRIGATED_PASTURE,
            inorganic=BasicProductionSystemScope1Method1Inorganic(
                calculation_method_scope1="1",
                applications=[
                    BasicProductionSystemScope1Method1InorganicApplicationsInner(Scope3Method1(
                        fertiliser_type=InorganicFertiliserType.UREA,
                        mass_applied_kg=Scope3Method1MassAppliedKg(value=2000),
                        calculation_method_scope3="1",
                    ))
                ],
            ),
            organic=OrganicFertilisersInput(applications=[]),
        )),
    )

    return PostBeefRequest(
        is_february_in_leap_year=False,
        electricity=PostBeefRequestElectricity(LocationBased(
            method="location",
            electricity_purchased_kwh=LocationBasedElectricityPurchasedKWh(value=5000),
            region=ElectricityRegion.QLD,
        )),
        herds=[herd],
    )

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
