# Scripts for submitting EAP CSV exports to the AIA Emissions Calculators API

The [AIA Environmental Accounting Platform (EAP)](https://www.aiaeap.com/) is an on-farm GHG emissions calculation engine developed by [Agricultural Innovation Australia](https://aginnovationaustralia.com.au). Free access to AIA's open-source code is supported by the Australian Government through funding from the _Improving Consistency of On-Farm Emissions Estimates Program_.

This repo contains Python scripts that read emissions data from CSV files exported by the EAP and submit it to the Emissions Calculators REST API that is part of the AIA EAP.

<p align='center'>
  <a href='https://aginnovationaustralia.com.au'>
    <img src='../../assets/logo-light.svg' alt='Agricultural Innovation Australia' />
  </a>
</p>

# The scripts

Each script targets a single commodity and carries out the full upload in one pass:

- reads the commodity's data from a key-value CSV file exported by the EAP, using [pandas](https://pandas.pydata.org/)
- assembles the values into the JSON payload the API expects
- submits the payload to the Emissions Calculators REST API over a mutually authenticated TLS (mTLS) connection, and returns the calculated result

The goal is a consistent, repeatable way to move each commodity's exported data into the platform, so the same process can be reused commodity by commodity rather than rebuilt each time.

## Configuration

The scripts connect using a client certificate and key for mTLS. These credential files are **not** included in this repository and must be supplied by each user. The file paths and the API endpoint are set near the top of each script and will need to be adjusted to match your own environment.

# Contributing and support

If you are looking for help using the tools available here, there are a number of resources available to you.

First of all, we aim to make the tools as easy to use as possible out of the box, and for users to be able to self service their own questions. Documentation for consuming the REST API is available online [here](https://docs.aiaplatform.com.au).

If you still have a question, feel free to [open a github issue](https://github.com/aginnovationaustralia/emissions-calculators-examples/issues/new) and fill in the template with as much context as possible. We aim to have a response to your question within 48 hours.

# License

![Creative Commons Attribution](../../assets/by.png)

This project is licensed under a [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) license.

All users of the Code must acknowledge AIA as the source and maintainer of the EAP Calculator Engine code. All users of the Code must acknowledge that free access to the Code is supported by the Australian Government through funding from the Improving Consistency of On-Farm Emissions Estimates Program.

The acknowledgement must be displayed in documentation, digital interfaces, or product materials where attribution of technical components is ordinarily provided.

This includes the right to display the [‘Powered by EAP’](https://www.aiaeap.com/branding) logo in any systems which directly or indirectly use the open-source code, in a way which is clearly visible to third-party clients/customers/users of those systems.

At a minimum, the acknowledgement must state:

> “This product incorporates the EAP Calculator Engine open-source code developed and maintained by Agricultural Innovation Australia Ltd. Free access to AIA’s open-source code is supported by the Australian Government through funding from the Improving Consistency of On-Farm Emissions Estimates Program”

Users may not imply or state endorsement by AIA, unless explicit written consent from AIA has been granted. Users must not imply or state endorsement by the Australian Government.

---

<p align="center">
Made with ❤️ by
</p>

<p align="center">
    <a href="https://exogee.com">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../../assets/exogee-white.svg">
            <img src="../../assets/exogee-black.svg" alt="Exogee">
        </picture>
    </a>
</p>
